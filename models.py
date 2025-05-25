import google.generativeai as genai

genai.configure(api_key="AIzaSyAWbwRrE_tugEn-F7rffyFgsiQVJrsWaek")

models = genai.list_models()

for model in models:
    print(f"Name: {model.name}")
    print(f"  Description: {model.description}")
    print(f"  Input Types: {model.input_token_limit} tokens")
    print(f"  Output Types: {model.output_token_limit} tokens")
    print(f"  Model Type: {model.model_family}")
    print("-" * 50)
