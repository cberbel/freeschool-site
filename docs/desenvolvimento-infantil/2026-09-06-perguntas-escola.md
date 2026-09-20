# Perguntas em aberto (responde o Cláudio — a escola é ele)

Nenhuma resposta bloqueia o trabalho — o sistema segue com o que tem e ajusta quando a resposta
chegar. Respostas entram como bloco "Respostas" no fim deste arquivo, com data.

**Sobre as pessoas**
1. Quem são hoje as avaliadoras das observações? No sistema aparecem "Claudio" e "Sonia" — é
   isso mesmo, são duas? Alguém mais vai entrar?
2. Quantas horas por semana cada uma consegue dedicar a pontuar janelas de 2 minutos (é
   rápido: ~15 segundos por entrada ao vivo; ~3 minutos por clipe gravado)?

**Sobre as salas e a rotina**
3. Onde e a que horas cada agrupada dorme (sesta)? Esse espaço tem câmera?
4. A que horas cada agrupada usa o pátio?
5. O avental/colete é usado o dia inteiro ou só em algumas atividades? (Importa para onde
   prender tag e marcador.)

**Sobre as câmeras e a rede**
6. Onde fica o gravador (NVR) das câmeras e como acessá-lo? Ele grava 24 h? Por quantos dias?
7. As câmeras estão ligadas ao NVR por cabo (PoE) ou alguma é Wi-Fi?
8. A câmera do pátio que "segue" (rastreio automático) pode ficar **travada num ponto fixo**,
   sem seguir ninguém? Isso tira a função de segurança dela — a direção aceita?
9. Podemos mudar o **fps e o bitrate** das câmeras (de 25 para 15 fps)? Isso altera também a
   gravação de segurança da escola.
10. Onde a "sala MEIO" está apontada hoje? Alguém mexe nela? (Cada mudança precisa ser
    registrada.)

**Sobre o registro de observação**
11. Nas entradas de agosto aparece "sala 1" — é a "sala 1a3"? Podemos corrigir no banco?
12. Os áudios de 04/08 e 24/08 são quase todos teste de microfone — está certo descartá-los
    como observação?

**Sobre espaço e energia**
13. Há um ponto de rede e uma tomada (de preferência com nobreak) onde possa ficar um
    computador ligado 24 h, perto do NVR?
14. Quem na escola pode, no fim do dia, colocar 5 gravadores para carregar (20 minutos)? (Só
    para o piloto de áudio, daqui a algumas semanas.)

**Sobre a cozinha**
15. O fluxo de foto da refeição (prato servido / prato devolvido) nunca rodou. Quem pode tirar
    as duas fotos por refeição, começando na próxima semana?

## Respostas (Cláudio, 07/09)

1. Avaliadoras: hoje Sonia e Cláudio; **vai ter mais gente em breve**, em três níveis (sênior,
   médio, júnior). → tabela `avaliadores` criada (nome, nível, horas/semana).
2. Horas: **Sonia trabalha 7 h/dia nas câmeras**; Cláudio 10 a 20 min/dia. → carga humana muito
   maior que a suposta na Revisão 2.1 (≈ 35 h/semana só da Sonia): corpus dourado e kappa deixam de
   ser gargalo; o gargalo vira captação e a ferramenta de pontuação (sliders, feitos em 07/09).
3. Sesta: **há uma sala do soninho com câmera**. → linha `soninho` em `salas_cameras`; qual câmera,
   no inventário T0.
4. Horário do pátio: **o sistema deve descobrir sozinho** (ocupação por câmera e hora) até o 3º dia
   de captação. → entrega do T1, não pergunta.
5. Avental/colete: varia; **vai ter uniforme**. → onde prender tag e marcador decide-se com o uniforme.
6. NVR: **no mezanino, ao lado do computador, na sala do Cláudio**. → o PC de captação fica ali;
   sem obra de rede.
7. Câmeras: **todas PoE**.
8. Câmera do pátio (TrackMix) pode ficar travada em ponto fixo, **como todas**.
9. fps e bitrate: **pode mudar à vontade**.
10. Câmeras fixas na parede, ninguém mexe; **giram e mudam de ângulo se for o caso** (cada mudança
    registrada em `eventos_ambiente`).
11. "sala 1" nas entradas de agosto **era só o valor padrão da página**, não uma sala. → as 32
    entradas de 04/08 ficam como estão, sem janela (testes de microfone); as 9 de 24/08 eram
    "sala 1a3" de verdade e continuam com janela. A página agora só aceita sala da lista.
12. Áudios de teste: irrelevante; o modelo já os marca como não avaliáveis.
13. Ponto de rede e tomada perto do NVR: **sim**.
14. Carregar gravadores: **Bárbara, ou quem ela delegar**.
15. Fotos da refeição: **por ora, Laís, no almoço**. Perguntas de volta (foto pelo zoom da câmera da
    sala? conferir cardápio pela câmera, automático?) → nota técnica
    [`2026-09-07-cameras-zoom-e-refeicao.md`](2026-09-07-cameras-zoom-e-refeicao.md).
16. Max = Maximiliano (registrado em `aluno_apelidos`).

Pergunta nova (07/09): **um agente pode operar as câmeras Reolink, dar zoom?** → mesma nota técnica.
