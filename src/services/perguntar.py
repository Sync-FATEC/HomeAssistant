import google.generativeai as genai

genai.configure(api_key="AIzaSyCAipNj2PSwG12WssCp9lKWflvtlO6R9GQ")

def perguntar_gemini(pergunta: str) -> str:
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f'''
    Você é um assistente pessoal inteligente, especializado em responder perguntas de forma clara e objetiva.
    Responda apenas com o texto necessário, sem explicações adicionais ou formatação complexa.
    O texto deve ser claro e direto, sem rodeios ou informações desnecessárias.
    Se a pergunta não puder ser respondida, responda com "Desculpe, não sei a resposta para isso.".

    Pergunta: {pergunta}
    '''

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "Desculpe, ocorreu um erro ao tentar responder sua pergunta."
