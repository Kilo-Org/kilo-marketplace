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

const { spawn } = require('child_process');
const os = require('os');

const toolName = "search_entries";
const configArgs = ["--prebuilt", "dataplex"];


const PROCESS_ENV_VARS = [
    'PATH', 'HOME', 'USER', 'TMPDIR', 'TEMP', 'TMP', 'SystemRoot', 'COMSPEC',
    'PATHEXT', 'NODE_EXTRA_CA_CERTS', 'HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY',
    'NPM_CONFIG_CACHE',
];
const DATAPLEX_ENV_VARS = [
    'DATAPLEX_PROJECT', 'GOOGLE_APPLICATION_CREDENTIALS', 'GOOGLE_CLOUD_PROJECT',
    'GOOGLE_CLOUD_QUOTA_PROJECT', 'CLOUDSDK_CONFIG',
];

function prepareEnvironment() {
    const env = {};
    for (const key of [...PROCESS_ENV_VARS, ...DATAPLEX_ENV_VARS]) {
        if (process.env[key] !== undefined) env[key] = process.env[key];
    }

    const prefix = 'CLAUDE_PLUGIN_OPTION_';
    for (const key of DATAPLEX_ENV_VARS) {
        const optionValue = process.env[`${prefix}${key}`];
        if (env[key] === undefined && optionValue !== undefined) env[key] = optionValue;
    }

    let userAgent = "skills";
    if (process.env.GEMINI_CLI === '1') {
        userAgent = "skills-geminicli";
    } else if (process.env.CLAUDECODE === '1') {
        userAgent = "skills-claudecode";
    } else if (process.env.CODEX_CI === '1') {
        userAgent = "skills-codex";
    }

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
