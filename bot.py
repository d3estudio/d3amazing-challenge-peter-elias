import os
import json
import csv
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from threading import Thread
from slack import WebClient
from flask import Flask, Response
from slackeventsapi import SlackEventAdapter
import ssl

ssl._create_default_https_context = ssl._create_unverified_context
# This `app` represents your existing Flask app
app = Flask(__name__)


turn = {"turnOn": "off"}

last = {"turnOn": False}

greetings = ["hi", "hello", "hello there", "hey", "olá", "oi"]

avaliar = ["avaliar", "sim"]


people = ["john", "bia", "thais", "vinicius", "elias", "iuri", "julio", "matheus", "romulo", "joao"]

# set datetime
dateTimeObj = datetime.now()
# format date for the brazilian model
br_date_format = dateTimeObj.strftime("%d/%b/%Y")

# obj para criacao do dict SCORES
obj = {
    "sender": "",
    "receiver": "",
    "score_social": None,
    "score_technical": None,
    "data_created": br_date_format
}

# rank as integers para ser usadas nos scores de social e technical
rank = ["1", "2", "3", "4", "5"]

grade = []
two = False

# path to the env file in root directory with slack credentials
env_path = Path('.') / '.env'
# load token
load_dotenv(dotenv_path=env_path)

# instantiating slack client
slack_client = WebClient(os.environ['SLACK_TOKEN'])

# conexao de evento com a api do slack
slack_events_adapter = SlackEventAdapter(
    os.environ['SIGNING_SECRET'], "/slack/events", app
)


@slack_events_adapter.on("app_mention")
def handle_message(event_data):
    def send_reply(value):
        event_data = value
        message = event_data["event"]
        # Handler to avoid error
        if message.get("subtype") is None:
            command = message.get("text")
            channel_id = message["channel"]
            # First question of the bot interaction
            if any(item in command.lower() for item in greetings):
                inicio = (
                        """
                            Olá <@%s> como posso ajuda-lo hoje ? 
                            1: Avaliar alguém ?
                            """
                        % message["user"]
                )
                slack_client.chat_postMessage(channel=channel_id, text=inicio)
                obj["sender"] = message["user"]
            
            elif any(item in command.lower() for item in avaliar) and turn["turnOn"] == "off":
                task = (
                    """
                    Quem você quer avaliar ?
                    """
                )
                slack_client.chat_postMessage(channel=channel_id, text=task)
                turn["turnOn"] = "off"
                return turn["turnOn"] == "off"

            elif any(item in command.lower() for item in people) and turn["turnOn"] == "off":
                response = (
                    """
                    Ok ! Qual nota vc quer dar para ele(a) ? :alien:\n\n ===================================================\n\n Primeira Pergunta ! :tada:\n\n 1: Qual nota você quer dar para o ele(a) no quesito "capacidade técnica para desenvolver as atividades" ?\n\n Notas disponiveis\n 1: Péssimo :white_frowning_face:\n 2: Ruim :slightly_frowning_face:\n 3: Regular :expressionless:\n 4: Bom :slightly_smiling_face:\n 5: Excelente :smiley:\n\n Exemplo de nota: 5\n\n Por favor siga o exemplo para não haver problemas ! Obrigado :spock-hand:
                    """
                )
                slack_client.chat_postMessage(channel=channel_id, text=response)
                # Adicionar valor de avaliado no dict
                obj["receiver"] = message["text"].split()[1]
                print(message["text"])
                turn["turnOn"] = "on"
                return turn["turnOn"], last

            elif any(item in command.lower() for item in rank) and turn["turnOn"] == "on":
                response2 = (
                    """ 
                    Segunda Pergunta ! :tada:\n\n 2: Qual nota você quer dar para o ele(a) no quesito "cooperação com a equipe / nível de responsabilidade com o projeto" ?\n\n Notas disponiveis\n 1: Péssimo :white_frowning_face:\n 2: Ruim :slightly_frowning_face:\n 3: Regular :expressionless:\n 4: Bom :slightly_smiling_face:\n 5: Excelente :smiley:\n\n Exemplo de nota: 5\n\n Por favor siga o exemplo para não haver problemas ! Obrigado :spock-hand:
                    """
                )

                slack_client.chat_postMessage(channel=channel_id, text=response2)
                # adicionar nota para obj
                obj["score_technical"] = int(message["text"].split()[1])
                turn["turnOn"] = "off"
                return turn["turnOn"]

            elif any(item in command.lower() for item in rank) and turn["turnOn"] == "off" and last["turnOn"] == False:

                response3 = (
                    """
                    Muito obrigado(a) por sua avaliaçao!!
                    """
                )
                print("CHECK AQUIII", int(message["text"].split()[1]))

                slack_client.chat_postMessage(channel=channel_id, text=response3)
                obj["score_social"] = int(message["text"].split()[1])

            # write data to csv file
            csv_file = open("peter.csv", "w")
            writer = csv.writer(csv_file)

            for key, value in obj.items():
                print(key, value)
                writer.writerow([key, value])

            csv_file.close()
            print(writer)


    # print para saber se os dados estao sendo passados para o dict
    print(obj)


    thread = Thread(target=send_reply, kwargs={"value": event_data})
    thread.start()
    return Response(status=200)


# Start the server on port 3000
if __name__ == "__main__":
    app.run(port=5000)
