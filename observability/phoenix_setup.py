import phoenix as px

from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor


import os

def setup_phoenix():
    os.makedirs("./phoenix_data", exist_ok=True)
    os.environ["PHOENIX_WORKING_DIR"] = "./phoenix_data"
    
    try:
        px.launch_app()
    except Exception as e:
        print(f"Phoenix app could not be launched (it may already be running): {e}")

    tracer_provider = register(
        project_name="enterprise-ai-evals",
        auto_instrument=True
    )

    LangChainInstrumentor().instrument(
        tracer_provider=tracer_provider
    )

    print("Phoenix tracing enabled")