"""App para predecir quien gana en una pelea de Pokemon.

La app nada más tiene una direccion/route a la raiz (por ejemplo
http://localhost:5000). Datos se pasan con un request the POST con
un cuerpo de JSON.

Por ejemplo:

input -> {"pokemon 1": "Pikachu", "pokemon 2": "Bulbasaur"}

output -> {
              "pokemon 1": "Pikachu",
              "pokemon 2": "Bulbasaur",
              "winner": "Bulbasaur",
              "confidence": 0.85
          }
"""

from flask import Flask, jsonify, request
import pickle
import pandas as pd

app = Flask(__name__)
app.secret_key = "pikapika"

# Vamos a cargar el modelo y los stats de los Pokemones. Usamos el
# nombre como ndex.
with open("model.pickle", "rb") as infile:
    model = pickle.load(infile)
stats = pd.read_pickle("stats.pickle")
stats.index = stats.pokename


def winner(pokemon1, pokemon2):
    """Determina quien gana y con que confianza.

    Arguments
    ---------
    pokemon1 : str
        Nombre del primer Pokemon en la pelea.
    pokemon2 : str
        Nombre del segundo Pokemon.

    Returns
    -------
    dict
        Nombres de los Pokemones combatantes, el ganador y la
        confianza que gana este Pokemon (de 0.5 a 1.0).
    """
    # Puede pasar que el request esta mal formado o se solicita un
    # Pokemon que no conocemos. En caso que todo esta bien sacamos los
    # stats de los dos Pokemon.
    try:
        first = stats.loc[pokemon1]
        second = stats.loc[pokemon2]
    except KeyError:
        return None
    # Unimos los stats y borramos las columnas con el nombre que no
    # usaremos.
    data = pd.concat([first, second]).drop("pokename")
    # predict espera una matrix entonces hay que convertir nuestro vector
    # a una matrix con una fila.
    data = data.as_matrix().reshape(1, -1)
    resp = model.predict_proba(data)
    # Predict proba nos da dos probabilidades. La primera es para la clase
    # "0" = pierde Pokemon 1 y la segunda es para "1" = gana el Pokemon 1.
    # También lo da como matrix de una fila. Entonces tenemos que sacar el
    # valor en la primera fila (0) y de la segunda columna (1).
    resp = resp[0, 1]
    # Si la probabilidad es > 0.5 gana el primer Pokemon, si no el segundo.
    winner = pokemon1 if resp > 0.5 else pokemon2
    conf = resp if resp > 0.5 else 1.0 - resp
    # Formateamos la respuesta como lo dicta la API.
    data = {
        "pokemon 1": pokemon1,
        "pokemon 2": pokemon2,
        "winner": winner,
        "confidence": conf
    }
    return data


@app.route("/", methods=["GET", "POST"])
def get_winner():
    """Accesso a la API REST.

    El body del request debería contener los pokemones que
    compiten. Para funcionar perfecto debería dar los siguiente
    codigos de estatus:

    metodo GET
    ----------
    200 con un mensaje motivador

    metodo POST
    -----------
    - 200 con la respuesta para input correcto
    - 400 con un mensaje de error para input malformado

    """
    body = request.get_json()
    # Si el request no esta como queremos hay que dar un error
    if "pokemon 1" not in body or "pokemon 2" not in body:
        return jsonify(error="invalid request format :("), 400
    result = winner(body["pokemon 1"], body["pokemon 2"])
    # result va ser None si no existe uno de los Pokemones...
    if result:
        return jsonify(result)
    else:
        return jsonify(error="Pokemon not found :("), 400


if __name__ == "__main__":
    # Inicia y corre la app en la puerta 5000
    app.run(debug=True)
