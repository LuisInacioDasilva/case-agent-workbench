import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ProviderError(RuntimeError):
    pass


class OllamaProvider:
    """Somente API local: nunca aceita URL fornecida pelo caso analisado."""

    endpoint = "http://127.0.0.1:11434/api/chat"

    def __init__(self, model: str | None = None, timeout: float = 45):
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen3:4b-instruct")
        self.timeout = timeout

    def complete(self, *, role: str, system: str, payload: dict, schema: dict) -> dict:
        body = json.dumps({
            "model": self.model,
            "stream": False,
            "format": schema,
            "options": {"temperature": 0},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
        }).encode("utf-8")
        request = Request(self.endpoint, data=body, headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                result = json.load(response)
            return json.loads(result["message"]["content"])
        except (HTTPError, URLError, TimeoutError, KeyError, ValueError) as exc:
            raise ProviderError(f"Ollama local indisponível ou resposta inválida ({role})") from exc


class DemoProvider:
    """Resposta determinística para testes e visualização; não é um LLM."""

    model = "demo-deterministico"

    def complete(self, *, role: str, system: str, payload: dict, schema: dict) -> dict:
        if role == "analyst":
            text = payload["case"].casefold()
            if any(term in text for term in ("áudio", "audio", "whatsapp", "codec")):
                category, doc_id = "audio", "KB-AUDIO-01"
                answer = "Verifique codec, contêiner e confirmação do provedor antes de considerar o áudio entregue."
            elif any(term in text for term in ("pedido", "erp", "orçamento")):
                category, doc_id = "order", "KB-ORDER-02"
                answer = "Compare identificador, último evento, versão e horário nas duas origens antes de corrigir o pedido."
            elif any(term in text for term in ("cadastro", "cliente", "duplic")):
                category, doc_id = "customer", "KB-CUSTOMER-03"
                answer = "Compare telefone, email e propostas vinculadas; não una registros só pelo nome."
            else:
                category, doc_id = "general", "KB-GENERAL-04"
                answer = "Faltam evidências para concluir. Localize o identificador do caso e os logs da origem."
            available = {item["id"] for item in payload["evidence"]}
            if doc_id not in available:
                doc_id = "KB-GENERAL-04" if "KB-GENERAL-04" in available else next(iter(available))
                answer = "A evidência recuperada é insuficiente; confira o caso antes de agir."
            return {"category": category, "answer": answer, "citations": [doc_id], "needs_human": True}
        if role == "reviewer":
            cited = set(payload["draft"].get("citations", []))
            available = {item["id"] for item in payload["evidence"]}
            return {"approved": bool(cited) and cited <= available, "reason": "Evidências locais verificadas; revisão humana ainda necessária."}
        raise ProviderError("unknown role")
