import boto3
import simplejson as json
import random
import string
import logging


dynamodbTableName = 'wordle_data'
# Defining the dynamo cliet
dynamodb = boto3.resource('dynamodb')
# getting the table
table = dynamodb.Table(dynamodbTableName)

#HTTP REQUESTS

getMethod = 'GET'
postMethod = 'POST'

gamesPath = '/games'
game_idPath = '/games/-game_id-'
guessPath = '/games/-game_id-/guesses'


def lambda_handler(event, context):
    try:
        # Extracting the http method
        httpMethod = event['httpMethod']
        path = event['path']

        # Takes the number of letters and creates a new game, returns the game id
        if httpMethod == postMethod and path == gamesPath:
            num_letters = int(json.loads(event['body'])['num_letters'])
            user_id = json.loads(event['body'])['user_id']
            print(user_id, num_letters)
            # Checking if the number of letters falls in the desired range
            if num_letters in range(5, 9):
                response_json = json.dumps(
                    startGame(num_letters, user_id))
                print(response_json)
                return {'statusCode': 201, 'body': response_json}
            return {'statusCode': 400, 'body': 'Invalid word length'}

        # Takes the game_id and returns the status of the game
        if httpMethod == getMethod and path == game_idPath:
            game_id = json.loads(event['body'])
            response = table.get_item(Key={'game_id': game_id['game_id']})
            if 'Item' in response:
                response_body = getGame(response)
                response_json = json.dumps(response_body)
                print(response_json)
                return {'statusCode': 200, 'body': response_json}

            return {'statusCode': 404, 'body': 'Game not found'}

        # Takes the game_id, guessed_word and returns the result based on the guessed_word
        if httpMethod == postMethod and path == guessPath:
            game_id = json.loads(event['body'])['game_id']
            guessed_word = (json.loads(event['body'])['guessed_word']).lower()
            response = table.get_item(Key={'game_id': game_id})

            if 'Item' in response:
                game_data = response['Item']['game_data']
                print(game_data)
                #Checking if it satisfies base conditions 
                if not guessed_word.isalpha() or len(guessed_word) != len(game_data['word']):
                    return {'statusCode': 400, 'body': 'Invalid guessed word'}
                elif game_data['remaining_turns'] == 0:
                    return {'statusCode': 400, 'body': 'Game over'}
                response_body = saveGuess(game_data, guessed_word, game_id)
                print(response_body)
                response_json = json.dumps(response_body)
                print(response_json)
                return {'statusCode': 200, 'body': response_json}
            return {'statusCode': 404, 'body': 'Game not found'}

        # Return a 404 error for any other request
        return {'statusCode': 404, 'body': {'message': 'Resource not found'}}
    
    except Exception as e:
        # Log the error message
        print(f'Error: {str(e)}')
        # Return a 500 error with the error message
        return {'statusCode': 500, 'body': {'message': 'Internal server error'}}


#Function used to start a new gaem
def startGame(num_letters, user_id):
    # Generate a random target word of the specified length
    wordlist = ['apple', 'banana', 'cherry', 'date', 'elder', 'fig', 'grape', 'hazel', 'indigo', 'juniper', 'kiwi', 'lemon', 'mango',
                'nectar', 'orange', 'peach', 'quince', 'rasp', 'straw', 'tanger', 'ugli', 'vanilla', 'water', 'xigua', 'yellow', 'zucchini']

    # Generate a random word with the specified number of letter
    word = random.choice([w for w in wordlist if len(w) == num_letters])

    # Generates a unique game_id
    temp_id = str(random.randint(1, 1000000))

    while 'Item' in table.get_item(Key={'game_id': temp_id}):
        temp_id = str(random.randint(1, 1000000))

    # Create a new game in DynamoDB
    game_data = {
        'user_id': user_id,
        'word': word,
        'remaining_turns': int(num_letters)+1,
        'guesses': []
    }
    table.put_item(Item={'game_id': temp_id, 'game_data': game_data})

    # Return the game ID
    return {'game_id': temp_id}

#Function used to get the game data from the game_id
def getGame(response):
    game_data = response['Item']['game_data']
    # Return the game status
    response_body = {
        'user_id': game_data['user_id'],
        'remaining_turns': game_data['remaining_turns'],
        'guesses': game_data['guesses']
    }
    return {'game_data': response_body}

#Function used to check the guessed word and returns the feedback
def saveGuess(game_data, guessed_word, game_id):
    # Check if the guessed word is the same as the target word
    target_word = game_data['word']
    if guessed_word == target_word:
        # If the guessed word is the same as the target word, mark it as correct
        feedback = 'correct'
    else:
        # Otherwise, mark each letter in the guessed word as either green, yellow, or gray
        feedback = []
        for i in range(len(guessed_word)):
            if guessed_word[i] == target_word[i]:
                feedback.append('green')
            elif guessed_word[i] in target_word:
                feedback.append('yellow')
            else:
                feedback.append('gray')

    # Add the guessed word to the list of guesses and decrement the remaining turns
    game_data['guesses'].append(guessed_word)
    game_data['remaining_turns'] -= 1

    # Update the game data in DynamoDB
    table.update_item(Key={'game_id': game_id}, UpdateExpression='SET game_data = :game_data',
                      ExpressionAttributeValues={':game_data': game_data})

    # Return the feedback for the guessed word
    return {'feedback': feedback}
