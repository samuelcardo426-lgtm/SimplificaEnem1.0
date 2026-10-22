import json
import random
import time
import streamlit as st

# 1. Configuração da Página
st.set_page_config(
    page_title="Simulado & Tutor ENEM - Ciências da Natureza",
    page_icon="🧬",
    layout="centered"
)

# 2. Carregamento do Banco de Dados JSON
@st.cache_data
def carregar_questoes():
    try:
        with open("banco_questoes.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

todas_questoes = carregar_questoes()

# 3. Inicialização Limpa de Estados de Sessão
if "iniciado" not in st.session_state:
    st.session_state.iniciado = False
if "finalizado" not in st.session_state:
    st.session_state.finalizado = False
if "questoes" not in st.session_state:
    st.session_state.questoes = []
if "indice" not in st.session_state:
    st.session_state.indice = 0
if "respostas" not in st.session_state:
    st.session_state.respostas = {}
if "modo" not in st.session_state:
    st.session_state.modo = "Sem Cronômetro"
if "mensagens_ia" not in st.session_state:
    st.session_state.mensagens_ia = [
        {"role": "assistant", "content": "Olá! Sou o teu tutor de Ciências da Natureza para o ENEM. Tens alguma dúvida sobre Física, Química ou Biologia?"}
    ]

# 4. Cabeçalho Principal
st.title("🧪 Plataforma de Estudos ENEM - Ciências da Natureza")
st.caption("Física, Química, Biologia e Tutor IA integrados")

# --- CRIAÇÃO DAS ABAS (TABS) ---
aba_simulado, aba_ia = st.tabs(["📝 Simulado ENEM", "🤖 Tutor IA (Tirar Dúvidas)"])

# ==========================================
# ABA 1: SIMULADO ENEM
# ==========================================
with aba_simulado:
    # --- TELA 1: CONFIGURAÇÃO ---
    if not st.session_state.iniciado and not st.session_state.finalizado:
        st.subheader("⚙️ Configurar Simulado")

        if not todas_questoes:
            st.error("⚠️ O arquivo `banco_questoes.json` não foi encontrado ou está vazio.")
            st.stop()

        anos = sorted(list(set(q["ano"] for q in todas_questoes)), reverse=True)
        materias = sorted(list(set(q["materia"] for q in todas_questoes)))
        niveis = sorted(list(set(q.get("nivel", "Médio") for q in todas_questoes)))

        filtro_ano = st.multiselect("Filtrar por Ano:", options=anos, default=anos, key="f_ano")
        filtro_materia = st.multiselect("Filtrar por Disciplina:", options=materias, default=materias, key="f_mat")
        filtro_nivel = st.multiselect("Filtrar por Nível:", options=niveis, default=niveis, key="f_niv")
        
        modo_jogo = st.radio(
            "Modo de Jogo:",
            options=["Sem Cronômetro", "Cronometrado (3 min por questão)"],
            index=0,
            key="r_modo"
        )

        filtradas = [
            q for q in todas_questoes
            if q["ano"] in filtro_ano 
            and q["materia"] in filtro_materia 
            and q.get("nivel", "Médio") in filtro_nivel
        ]

        st.info(f"📌 Questões disponíveis para esta seleção: **{len(filtradas)}**")

        if filtradas:
            qtd = st.slider("Número de questões no simulado:", min_value=1, max_value=len(filtradas), value=min(5, len(filtradas)))
            embaralhar = st.checkbox("Embaralhar ordem das questões", value=True)

            if st.button("🚀 Iniciar Simulado", type="primary"):
                if embaralhar:
                    random.shuffle(filtradas)
                
                st.session_state.questoes = filtradas[:qtd]
                st.session_state.indice = 0
                st.session_state.respostas = {}
                st.session_state.modo = modo_jogo
                st.session_state.iniciado = True
                st.session_state.finalizado = False
                
                # Limpa temporizadores antigos
                for k in list(st.session_state.keys()):
                    if k.startswith("timer_"):
                        del st.session_state[k]
                
                st.rerun()

    # --- TELA 2: EXECUÇÃO DO SIMULADO ---
    elif st.session_state.iniciado and not st.session_state.finalizado:
        idx = st.session_state.indice
        questoes = st.session_state.questoes
        q = questoes[idx]

        st.progress((idx + 1) / len(questoes))

        col1, col2 = st.columns([2, 2])
        with col1:
            st.subheader(f"Questão {idx + 1} de {len(questoes)}")
        with col2:
            st.markdown(f"**{q['materia']}** | {q['ano']} | **Nível:** {q.get('nivel', 'Médio')}")

        # Gerenciamento de tempo individual por questão
        timer_key = f"timer_{idx}"
        if timer_key not in st.session_state:
            st.session_state[timer_key] = time.time()

        tempo_esgotado = False
        if st.session_state.modo == "Cronometrado (3 min por questão)":
            decorrido = time.time() - st.session_state[timer_key]
            restante = 180 - int(decorrido)
            if restante <= 0:
                tempo_esgotado = True
                st.error("⏰ O tempo limite de 3 minutos esgotou para esta questão!")
            else:
                mins, secs = divmod(restante, 60)
                st.warning(f"⏱️ Tempo restante: **{mins:02d}:{secs:02d}**")

        st.write(f"**Texto Base:** {q['enunciado']}")
        st.write(f"**Comando:** {q['pergunta']}")

        ja_respondido = idx in st.session_state.respostas
        opcoes = list(q["opcoes"].keys())
        
        resp_salva = st.session_state.respostas.get(idx, None)
        indice_default = 0
        if resp_salva and resp_salva in opcoes:
            indice_default = opcoes.index(resp_salva)

        desativado = ja_respondido or tempo_esgotado

        escolha = st.radio(
            "Alternativas:",
            options=opcoes,
            index=indice_default,
            format_func=lambda x: f"({x}) {q['opcoes'][x]}",
            key=f"radio_{idx}",
            disabled=desativado
        )

        if ja_respondido:
            resp = st.session_state.respostas[idx]
            if resp == q["resposta_correta"]:
                st.success("✨ Resposta Correta!")
            elif resp == "TIMEOUT":
                st.error("⏰ Questão não respondida a tempo.")
            else:
                st.error(f"❌ Resposta Incorreta. A correta era **({q['resposta_correta']})**.")
            st.info(f"**Explicação:** {q['explicacao']}")
        elif tempo_esgotado:
            if st.button("Registrar como Não Respondida (Tempo Esgotado)", type="primary"):
                st.session_state.respostas[idx] = "TIMEOUT"
                st.rerun()
        else:
            if st.button("Confirmar Resposta", type="primary"):
                st.session_state.respostas[idx] = escolha
                st.rerun()

        st.divider()
        col_ant, col_prox = st.columns(2)
        
        with col_ant:
            if idx > 0:
                if st.button("⬅️ Questão Anterior"):
                    st.session_state.indice -= 1
                    st.rerun()

        with col_prox:
            if idx + 1 < len(questoes):
                if st.button("Próxima Questão ➡️"):
                    st.session_state.indice += 1
                    st.rerun()
            else:
                if st.button("Finalizar Simulado 🏆", type="primary"):
                    st.session_state.iniciado = False
                    st.session_state.finalizado = True
                    st.rerun()

    # --- TELA 3: RESULTADO ---
    elif st.session_state.finalizado:
        st.header("🎉 Simulado Concluído!")

        questoes = st.session_state.questoes
        total = len(questoes)
        acertos = 0

        for i, q in enumerate(questoes):
            if st.session_state.respostas.get(i) == q["resposta_correta"]:
                acertos += 1

        porcentagem = (acertos / total) * 100 if total > 0 else 0

        st.metric(label="Desempenho Geral", value=f"{acertos} de {total}", delta=f"{porcentagem:.1f}%")

        if porcentagem >= 70:
            st.balloons()
            st.success("Excelente desempenho! Continue praticando.")
        else:
            st.warning("Bom trabalho! Revise os pontos de maior dificuldade.")

        st.divider()

        if st.button("🔄 Refazer / Novo Simulado"):
            st.session_state.iniciado = False
            st.session_state.finalizado = False
            st.session_state.indice = 0
            st.session_state.respostas = {}
            for k in list(st.session_state.keys()):
                if k.startswith("timer_"):
                    del st.session_state[k]
            st.rerun()

# ==========================================
# ABA 2: TUTOR IA (TIRAR DÚVIDAS)
# ==========================================
with aba_ia:
    st.header("🤖 Tutor Inteligente - Ciências da Natureza")
    st.write("Escreve a tua dúvida sobre Física, Química ou Biologia. Podes perguntar sobre conceitos, fórmulas ou matérias que caem no ENEM.")

    with st.expander("⚙️ Configurações da IA (Opcional)"):
        st.info("Para ativar respostas inteligentes automáticas online, podes integrar a tua chave de API da OpenAI ou Google Gemini. Caso contrário, podes usar este espaço para registrar anotações ou simular interações.")
        api_key_input = st.text_input("Chave de API (OpenAI / Gemini):", type="password")

    for mensagem in st.session_state.mensagens_ia:
        with st.chat_message(mensagem["role"]):
            st.markdown(mensagem["content"])

    if prompt := st.chat_input("Ex: Explique a Lei de Faraday na Física..."):
        st.session_state.mensagens_ia.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if not api_key_input:
                resposta_assistente = f"Recebi a tua dúvida sobre: *'{prompt}'*. Como estás a correr o aplicativo localmente sem uma chave de API ativa, este é um espaço de chat simulado. Para respostas automáticas avançadas em tempo real, insere a tua chave de API nas configurações acima!"
            else:
                resposta_assistente = "Chave detetada! (Integração de API pronta para ser acoplada ao modelo escolhido)."
            
            st.markdown(resposta_assistente)
            st.session_state.mensagens_ia.append({"role": "assistant", "content": resposta_assistente})
