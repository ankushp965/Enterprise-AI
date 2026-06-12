import phoenix as px

from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor


def setup_phoenix():
    px.launch_app()

    tracer_provider = register(
        project_name="enterprise-ai-evals",
        auto_instrument=True
    )

    LangChainInstrumentor().instrument(
        tracer_provider=tracer_provider
    )

    print("Phoenix tracing enabled")