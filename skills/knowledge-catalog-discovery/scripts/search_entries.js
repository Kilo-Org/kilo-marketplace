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

const toolName = "search_entries";
const configArgs = ["--prebuilt", "dataplex"];


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


	return { env, userAgent };
}

function main() {
    const { env, userAgent } = prepareEnvironment();
    const args = process.argv.slice(2);

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

main();
