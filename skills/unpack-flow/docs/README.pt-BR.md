# UnpackFlow — extração aninhada sem vigilância

[English](../README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [हिन्दी](README.hi.md) · [العربية](README.ar.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [日本語](README.ja.md) · [Русский](README.ru.md)

Com `-r`, se o nome de saída já existir, o UnpackFlow acrescenta a pasta de origem, como `sample-backup-legacy-set-unpacked`, e usa `-2`, `-3` nas colisões seguintes, sem sobrescrever nem ignorar resultados.

A suíte pequena `unpack-flow-minimal-testcases-v1.zip` cobre ZIP, TAR.GZ, Unicode, arquivos aninhados, `part01.exe` multipartido e uma falha esperada por volume ausente, sem aplicativos grandes e sem executar o SFX.

A validação nativa usa dados sintéticos em `/data/unpack-flow-testcases`; o caminho pode ser alterado com `UNPACK_FLOW_TEST_ROOT`. Suítes grandes são opcionais e reservadas para desempenho ou compatibilidade adicional.

UnpackFlow processa distribuições de software, conjuntos de dados, backups, ativos de mídia e outros arquivos grandes. Ele encontra o primeiro volume, extrai camadas em sequência e mostra pacote, fase, nível e tempo.

## Uso e instalação

Use `unpack-flow list 'Archive*'`, `plan`, `unpack-flow 'Archive*'` e `status`. Linux requer Bash; Windows, PowerShell e 7-Zip; macOS, PowerShell 7+ e `7zz`. `scripts/build-release.sh` cria três pacotes e SHA-256.

Python não é necessário para executar `unpack-flow` nem extrair arquivos. Python 3 é usado somente para instalar automaticamente o Skill no Linux/macOS com `install_local.py` ou `install_local.sh` e para a auditoria Python. No Windows, `install_local.ps1` usa apenas PowerShell; a cópia manual do Skill também dispensa Python.

## Fluxos de extração compatíveis

O UnpackFlow extrai em lote diretórios e padrões, abre arquivos aninhados camada por camada e identifica o primeiro volume de conjuntos RAR multipartes. Também inspeciona autoextratores RAR sem executar EXE desconhecidos. É adequado para distribuições de software, dados, backups, mídia, logs e imagens ISO ou WIM.

Por padrão, percorre até 10 camadas internas. Um arquivo interno danificado ou incompleto é preservado, registrado e ignorado enquanto os demais continuam; use `-StopOnError` para parar no primeiro erro.

## Exemplos de aprendizado

Use `list`, `plan`, `start`, `status`, `log` e `wait` para backups, dados, logs, software ou arquivos multipartes. Jogos são apenas um exemplo, não o limite do produto.

Nos três sistemas, `run` permanece em primeiro plano mostrando o progresso, enquanto `start` inicia uma tarefa em segundo plano e retorna o ID.

Durante operações longas do 7-Zip ou UnRAR, o tempo é atualizado a cada segundo e um sinal de atividade é gravado a cada 30 segundos.

No macOS e Windows, `start` desconecta todos os fluxos interativos; o progresso fica apenas no log, sem sequências ANSI ou bipes do terminal.

Use `-r` ou `-Recursive` para localizar todos os arquivos em subpastas e extrair camadas internas; conflitos de nome são gravados com segurança como `nome-unpacked`.

`unpack-flow run *` também é aceito. Mesmo após a expansão de `*` pelo shell, a varredura mantém apenas arquivos únicos e primeiros volumes como `part1.exe`, `part1.rar`, `.7z.001` ou `.zip.001`, descartando `.sha256`, arquivos alheios e volumes posteriores.

`unpack-flow help` mostra a referência combinada em inglês e chinês simplificado.

## Tarefas em segundo plano e logs

`unpack-flow start "arquivo" -Output "destino"` inicia a extração em segundo plano e retorna um ID. Use `unpack-flow status [id]`, `unpack-flow log [id]` e `unpack-flow wait [id]`; sem ID, vale a tarefa mais recente. Os logs ficam em `%LOCALAPPDATA%\unpack-flow\state` no Windows e `~/.local/state/unpack-flow` no macOS/Linux.

TAR, TAR.GZ/TGZ e GZ independente são compatíveis. Depois do 7-Zip, o programa tenta conforme o formato UnRAR, `tar`, GZip ou ZIP nativo, limpando cada tentativa com falha; esgotadas as opções, preserva o arquivo, registra o erro e continua com o próximo, sem repetição infinita.

Linux x64 inclui o UnRAR 7.23 oficial. Windows x64/ARM64 inclui o 7-Zip 26.02 oficial completo; x64 também inclui UnRAR. Os pacotes e as licenças originais são preservados.

## Início rápido completo

```bash
unpack-flow list '/data/archives/*'
unpack-flow plan '/data/archives/backup.part1.rar'
unpack-flow run '/data/archives/*' -Output '/data/extracted'
```

Para executar em segundo plano:

```bash
unpack-flow start '/data/archives/*' -Output '/data/extracted'
unpack-flow status
unpack-flow log
unpack-flow wait
```

`run` permanece em primeiro plano; `start` retorna imediatamente um ID. Os arquivos de origem são preservados nos dois modos.

## Instalar a ferramenta de linha de comando

### Linux

```bash
./install-linux.sh --check
./install-linux.sh
unpack-flow version
```

### macOS

```bash
./install-macos.sh --check
./install-macos.sh
unpack-flow version
```

### Windows

```bat
install.bat -Check
install.bat
unpack-flow version
```

As verificações informam dependências ausentes, mas não instalam software do sistema automaticamente.

## Recursão, logs e falhas

Use `-r` ou `-Recursive` para procurar arquivos em subpastas e abrir camadas internas. O limite padrão é de 10 camadas internas.

| Plataforma | Diretório de estado padrão |
|---|---|
| Windows | `%LOCALAPPDATA%\unpack-flow\state` |
| Linux/macOS | `${XDG_STATE_HOME:-$HOME/.local/state}/unpack-flow` |

O UnpackFlow usa uma cadeia limitada: 7-Zip, UnRAR para RAR e ferramentas nativas adequadas para TAR, GZ ou ZIP. Cada tentativa incompleta é limpa. Se todas falharem, o arquivo original é preservado, o erro é registrado e o processamento continua. Use `-StopOnError` apenas para parar na primeira falha.

## Testes e instalação como Agent Skill

```bash
bash tests/generate-minimal-public-suite.sh
bash tests/test-minimal-public-suite.sh
pwsh -NoProfile -File tests/test-minimal-public-suite.ps1
scripts/install_local.sh .
```

No Windows, instale o Skill com `scripts/install_local.ps1`. Python não é necessário para extrair arquivos; ele é usado apenas no instalador automatizado do Skill para Linux/macOS e na auditoria Python.

## Segurança e suporte

Preserva fontes, não sobrescreve destinos nem executa EXE desconhecidos. Suporte: [once-email.com](https://once-email.com). MIT, versão 2.1.2.

Publicador, mantenedor e site oficial: [once-email.com](https://once-email.com). Criadora e desenvolvedora: helen.jar. Projeto no GitHub: [pangxin12345/unpack-flow](https://github.com/pangxin12345/unpack-flow). Para dúvidas, escreva para [tiantuowl@gmail.com](mailto:tiantuowl@gmail.com).
