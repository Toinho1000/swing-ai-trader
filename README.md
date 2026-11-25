# SWING AI TRADER V2.0

Painel educativo para consultar cotações e histórico de ações brasileiras pela API brapi e estudar indicadores.

- Sem conexão com corretoras e sem execução de ordens.
- Não é recomendação de investimento.
- Dados podem ter atraso, limites ou indisponibilidade.
- A documentação da brapi informa que o plano gratuito inclui 15.000 requisições/mês, até 3 meses de histórico e atualização aproximada de 30 minutos; confira os termos atuais.
- Teste sem token documentado para PETR4, VALE3, MGLU3 e ITUB4.
- Não coloque tokens ou senhas no código público.

## Atualização no GitHub
Substitua `app.py` e `requirements.txt` na raiz do repositório pelos arquivos desta versão e faça Commit changes. O Streamlit detectará a alteração e reiniciará o app.

## Execução local
`pip install -r requirements.txt`
`streamlit run app.py`

Documentação: https://brapi.dev/docs
Histórico: https://brapi.dev/docs/acoes/historico
