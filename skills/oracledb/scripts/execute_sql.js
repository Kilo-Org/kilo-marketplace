#!/usr/bin/env node

// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

const { spawn, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

const toolName = "execute_sql";
const configArgs = ["--prebuilt", "oracledb"];

const OPTIONAL_VARS_TO_OMIT_IF_EMPTY = [
    'ORACLE_WALLET',
    'ORACLE_USE_OCI',
];


function mergeEnvVars(env) {
	if (process.env.GEMINI_CLI === '1') {
		const envPath = path.resolve(__dirname, '../../../.env');
		if (fs.existsSync(envPath)) {
			const envContent = fs.readFileSync(envPath, 'utf-8');
			envContent.split('\n').forEach(line => {
				const trimmed = line.trim();
				if (trimmed && !trimmed.startsWith('#')) {
					const splitIdx = trimmed.indexOf('=');
					if (splitIdx !== -1) {
						const key = trimmed.slice(0, splitIdx).trim();
						let value = trimmed.slice(splitIdx + 1).trim();
						value = value.replace(/(^['"]|['"]$)/g, '');
						if (env[key] === undefined) {
							env[key] = value;
						}
					}
				}
			});
		}
	} else if (process.env.CLAUDECODE === '1') {
		const prefix = 'CLAUDE_PLUGIN_OPTION_';
		for (const key in process.env) {
			if (key.startsWith(prefix)) {
				env[key.substring(prefix.length)] = process.env[key];
			}
		}
	}
}

function prepareEnvironment() {
	let env = { ...process.env };
	let userAgent = "skills";
	if (process.env.GEMINI_CLI === '1') {
		userAgent = "skills-geminicli";
	} else if (process.env.CLAUDECODE === '1') {
		userAgent = "skills-claudecode";
	} else if (process.env.CODEX_CI === '1') {
        userAgent = "skills-codex";
    }
	mergeEnvVars(env);

	OPTIONAL_VARS_TO_OMIT_IF_EMPTY.forEach(varName => {
		if (env[varName] === '') {
			delete env[varName];
		}
	});


	return { env, userAgent };
}

function sanitizeSql(sql) {
    let output = '';
    let i = 0;
    while (i < sql.length) {
        const char = sql[i];
        const next = sql[i + 1];
        if (char === '-' && next === '-') {
            output += '  ';
            i += 2;
            while (i < sql.length && sql[i] !== '\n') {
                output += ' ';
                i += 1;
            }
            continue;
        }
        if (char === '/' && next === '*') {
            output += '  ';
            i += 2;
            let closed = false;
            while (i < sql.length) {
                if (sql[i] === '*' && sql[i + 1] === '/') {
                    output += '  ';
                    i += 2;
                    closed = true;
                    break;
                }
                output += sql[i] === '\n' ? '\n' : ' ';
                i += 1;
            }
            if (!closed) throw new Error('Unterminated SQL block comment');
            continue;
        }
        if ((char === 'q' || char === 'Q') && next === "'" && i + 2 < sql.length) {
            const opener = sql[i + 2];
            const pairs = { '[': ']', '{': '}', '(': ')', '<': '>' };
            const closer = pairs[opener] || opener;
            output += '   ';
            i += 3;
            let closed = false;
            while (i < sql.length) {
                if (sql[i] === closer && sql[i + 1] === "'") {
                    output += '  ';
                    i += 2;
                    closed = true;
                    break;
                }
                output += sql[i] === '\n' ? '\n' : ' ';
                i += 1;
            }
            if (!closed) throw new Error('Unterminated Oracle alternative-quoted string');
            continue;
        }
        if (char === "'" || char === '"') {
            const quote = char;
            output += ' ';
            i += 1;
            let closed = false;
            while (i < sql.length) {
                if (sql[i] === quote) {
                    if (sql[i + 1] === quote) {
                        output += '  ';
                        i += 2;
                        continue;
                    }
                    output += ' ';
                    i += 1;
                    closed = true;
                    break;
                }
                output += sql[i] === '\n' ? '\n' : ' ';
                i += 1;
            }
            if (!closed) throw new Error('Unterminated SQL quoted value');
            continue;
        }
        output += char;
        i += 1;
    }
    return output;
}

function assertReadOnlySql(sql) {
    if (typeof sql !== 'string' || !sql.trim()) {
        throw new Error('The sql parameter must be a non-empty string');
    }
    const sanitized = sanitizeSql(sql);
    const semicolons = [...sanitized.matchAll(/;/g)].map(match => match.index);
    if (semicolons.length > 1) {
        throw new Error('Only one SQL statement is allowed in read-only mode');
    }
    let statement;
    if (semicolons.length === 1) {
        const semicolon = semicolons[0];
        if (!sanitized.slice(0, semicolon).trim() || sanitized.slice(semicolon + 1).trim()) {
            throw new Error('A semicolon is permitted only at the end of one read-only statement');
        }
        statement = sanitized.slice(0, semicolon).trim();
    } else {
        statement = sanitized.trim();
    }
    const firstKeyword = (statement.match(/^([A-Za-z]+)/) || [])[1];
    if (!firstKeyword || !['SELECT', 'WITH'].includes(firstKeyword.toUpperCase())) {
        throw new Error('Read-only mode accepts only SELECT or WITH queries');
    }
    const forbidden = /\b(INSERT|UPDATE|DELETE|MERGE|UPSERT|CREATE|ALTER|DROP|TRUNCATE|RENAME|GRANT|REVOKE|CALL|EXECUTE|BEGIN|DECLARE|COMMIT|ROLLBACK|SAVEPOINT|LOCK|COPY|DO|FUNCTION|PROCEDURE)\b/i;
    const match = statement.match(forbidden);
    if (match) {
        throw new Error(`Read-only mode rejects SQL keyword ${match[1].toUpperCase()}`);
    }
    if (/\bFOR\s+(UPDATE|SHARE)\b/i.test(statement) || /\bSELECT\s+.*\bINTO\b/is.test(statement)) {
        throw new Error('Read-only mode rejects SELECT INTO and row-locking queries');
    }
}

function parseInvocationArgs(rawArgs) {
    let dangerous = false;
    let confirmed = false;
    const args = [];
    for (const arg of rawArgs) {
        if (arg === '--dangerous') {
            dangerous = true;
        } else if (arg === '--confirm-dangerous-sql=EXECUTE') {
            confirmed = true;
        } else {
            args.push(arg);
        }
    }
    if (dangerous !== confirmed) {
        throw new Error('Non-read SQL requires both --dangerous and --confirm-dangerous-sql=EXECUTE');
    }
    if (args.length !== 1) {
        throw new Error('Expected exactly one JSON argument containing the sql parameter');
    }
    let payload;
    try {
        payload = JSON.parse(args[0]);
    } catch (error) {
        throw new Error(`Invalid JSON argument: ${error.message}`);
    }
    if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
        throw new Error('The invocation argument must be a JSON object');
    }
    if (!dangerous) {
        assertReadOnlySql(payload.sql);
    }
    return args;
}

function main() {
    const { env, userAgent } = prepareEnvironment();
    let args;
    try {
        args = parseInvocationArgs(process.argv.slice(2));
    } catch (error) {
        console.error(`Refusing SQL execution: ${error.message}`);
        process.exit(2);
    }

		const command = os.platform() === 'win32' ? 'npx.cmd' : 'npx';
		const processedArgs = os.platform() === 'win32' ? args.map(arg => arg.includes('"') ? '"' + arg.replace(/"/g, '""') + '"' : arg) : args;
		const npxArgs = ["--yes", "@toolbox-sdk/server@1.1.0", "--log-level", "error", ...configArgs, "invoke", toolName, "--user-agent-metadata", userAgent, ...processedArgs];

		const child = spawn(command, npxArgs, { shell: os.platform() === 'win32', stdio: 'inherit', env });


    child.on('close', (code) => {
        process.exit(code);
    });

    child.on('error', (err) => {
        console.error("Error executing toolbox:", err);
        process.exit(1);
    });
}

if (require.main === module) {
    main();
}

module.exports = { assertReadOnlySql };
