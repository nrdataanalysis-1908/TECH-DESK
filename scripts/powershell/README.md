# Adaptadores PowerShell

As rotinas administrativas serão implementadas aqui, de forma modular.

## Requisitos por script

- Validar versão do Windows e privilégios.
- Receber parâmetros explícitos e tipados.
- Utilizar `SupportsShouldProcess` e `-WhatIf` quando aplicável.
- Retornar códigos de saída previsíveis.
- Aplicar timeout e tratamento de exceções.
- Registrar início, término, duração e resultado.
- Nunca incorporar credenciais.
- Nunca executar texto livre como comando.
- Documentar impacto, reversibilidade e pré-condições.

Nenhuma rotina destrutiva é habilitada nesta etapa inicial.
