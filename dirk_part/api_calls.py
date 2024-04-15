import json
import requests
from datetime import datetime
import anthropic
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import openai


def claude_first_call(userprompt):
    client = anthropic.Anthropic(
        api_key="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",
    )
    
    try:
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            temperature=0.2,
            system=f"""Extraheer de volgende informatie uit de gegeven tekst. 
            Als een variabele niet exact kan worden bepaald uit de gegeven tekst, vermeld dit dan, NOOIT iets verzinnen! 
            
            Voor het variabel 'letselschade' vul 'Ja' of 'Nee' in met een zeer korte en bondige reden waarom en specifiek wat voor een schade/waar.
            Voor extra duidelijkheid is hier de definitie van letselschade:
            defenitie letselschade: aansprakelijkheidsrecht (letselschaderecht) - lichamelijk of geestelijk letsel dat door een ander is veroorzaakt en kan leiden tot immateriële schadevergoeding of smartengeld.

            Formatteren als een JSON-object: JSON-format: {{\\n\"Letselschade\": \"\",\\n\"Claim\": \"\",\\n\"Wat is er gebeurd\": \"\",\\n\"Hoe is het gebeurd\": \"\",\\n}} """,
            messages=[{"role": "user", "content": userprompt}]
        )
        
        content_text = ""
        for content in message.content:
            if hasattr(content, 'text'):
                content_text += content.text
        
        print(content_text)
        return content_text
    except Exception as e:
        print(f"Error in claude_put_in_json: {str(e)}")
        return None


#remake the claude call only for openai and use the gpt 4 preview model and set it in json mode
def openai_first_call(userprompt):
    try:
        message = openai.Completion.create(
            engine="gpt-4-preview",
            prompt=userprompt,
            max_tokens=1000,
            temperature=0.2,
            response_format={ "type": "json_object" }
            api_key="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"
        )
        
        content_text = ""
        for content in message.choices:
            if hasattr(content, 'text'):
                content_text += content.text
        
        print(content_text)
        return content_text
    except Exception as e:
        print(f"Error in claude_put_in_json: {str(e)}")
        return None
        


































def process_lead(json_data):
    input_variables = list(json_data.keys())
    additional_variables = ["Letselschade", "Type ongeval", "Tijd sinds ongeval"]
    expected_variables = input_variables + additional_variables
    while True:
        prompt = f"""Op basis van de volgende JSON-gegevens, vul de ontbrekende variabelen in en voeg de velden 'Letselschade' en 'Type ongeval' toe:\n\n{json.dumps(json_data, indent=2)}
        
        Definitie van letselschade: Letselschade is de schade die iemand lijdt als gevolg van een ongeval of gebeurtenis waarvoor een ander aansprakelijk is. 
        Het omvat alle nadelige gevolgen op lichamelijk, geestelijk en financieel gebied die voortvloeien uit het letsel, zoals medische kosten, inkomstenderving, extra uitgaven en smartengeld.
        
        Voor het veld 'Letselschade', vul 'Ja' of 'Nee' in met een zeer korte en bondige reden waarom en specifiek wat voor een schade/waar.
            
        Opties voor type ongeval: Medische aansprakelijkheid, verkeersongevallen, bedrijfsongevallen, ongevallen door dieren, ongevallen door gebrekkig wegdek, of iets anders. Kies slechts één optie zonder verdere uitleg.
        Als er geen antwoord is op een veld, vul dan 'geen gegevens' in.
        Bereken ook de tijd die is verstreken sinds het ongeval plaatsvond en voeg dit toe als 'Tijd sinds ongeval' in het formaat 'X dagen/maanden/jaren'.
        Mocht het variabel in the json 'Looptijd zaak' geen datum aangeven of aangeven dat er geen zaak loopt.
        Huidige datum: {datetime.now().strftime('%Y-%m-%d')}
        """
        response_text = claude_put_in_json(prompt)
        try:
            processed_lead = json.loads(response_text)

            # Check if all expected variables are present in the output
            if all(var in processed_lead for var in expected_variables):
                return processed_lead
            else:
                print("Output does not contain all expected variables. Resending prompt...")

        except json.JSONDecodeError:
            print("Failed to parse JSON response from Claude API. Resending prompt...")







def judge_lead(processed_lead):
    system_prompt = """
    Je bent een AI-systeem dat bepaalt of een zaak moet worden doorgestuurd naar een letselschadeadvocaat of dat de zaak niet geschikt is voor de advocaat.

    Beoordeel de zaak op basis van de volgende criteria:

    Is er sprake van letselschade?
    defenitie letselschade: aansprakelijkheidsrecht (letselschaderecht) - lichamelijk of geestelijk letsel dat door een ander is veroorzaakt en kan leiden tot immateriële schadevergoeding of smartengeld.
    
    Nee -> Output "zaak niet aangenomen vanwege afwezigheid van letselschade" en return direct.
    Ja -> Ga door naar de volgende vraag.
    Type ongeval?
    Medische aansprakelijkheid -> Output "zaak wordt niet aangenomen vanwege medische aansprakelijkheid" en return direct.
    Als het type ongeval één van de volgende is: verkeersongevallen, bedrijfsongevallen, ongevallen door dieren, ongevallen door gebrekkig wegdek -> Ga door naar de volgende vraag.
    
    WANNEER heeft ongeval plaatsgevonden?
    Minder dan een jaar geleden -> Output "zaak aangenomen" en return direct.
    Meer dan een jaar geleden -> KIJK NAAR DE LOOPTIJD VAN DE ZAAK.

    Hoe lang loopt deze zaak al actief?
    MINDER dan 1 jaar -> Output "zaak geaccepteerd" en return.
    MEER dan 1 jaar -> Output "zaak niet geaccepteerd" en return.

    Geef het oordeel als een JSON-object met een 'beslissing' veld met de toepasselijke boodschap en een 'reden' veld met een beknopte uitleg van de beslissing. De 'reden' moet bondig zijn en de specifieke criteria vermelden die tot de beslissing hebben geleid.
    """

    user_prompt = f"""
    Hier is de processed lead data:
    {json.dumps(processed_lead, indent=2)}

    Beoordeel de case op basis van de gegeven criteria en geef het oordeel terug als een JSON-object.
    """

    response_text = claude_final_boss(system_prompt,  user_prompt)
    try:
        judgment = json.loads(response_text)
        return judgment
    except json.JSONDecodeError:
        raise Exception("Failed to parse JSON response from Claude API")











def claude_final_boss(systemprompt, userprompt):
    client = anthropic.Anthropic(
        api_key="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",
    )
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        temperature=0.2,
        system=systemprompt,
        messages=[
            {"role": "user", "content": userprompt}
        ]
    )
    for content in message.content:
        if hasattr(content, 'text'):
            return content.text

