import boto3
import simplejson as json
import random
import string
import logging
from PyDictionary import PyDictionary
import inflect

#Dynamo Table
dynamodbTableName = 'wordle_data'
# Defining the dynamo cliet
dynamodb = boto3.resource('dynamodb')
# getting the table
table = dynamodb.Table(dynamodbTableName)

#HTTP REQUESTS
# Extracting the http method
httpMethod = event['httpMethod']
getMethod = 'GET'
postMethod = 'POST'

#Creating PyDictionary and Inflict instances to help us check if the word is valid or not
dictionary = PyDictionary()
engine = inflect.engine()


def lambda_handler(event, context):
    try:
        # Takes the number of letters and creates a new game, returns the game id
        if httpMethod == postMethod and event['resource'] == '/games':
            num_letters = int(json.loads(event['body'])['num_letters'])
            user_id = json.loads(event['body'])['user_id']
            game_mode = json.loads(event['body'])['game_mode']
            print(user_id, num_letters,game_mode)
            # Checking if the number of letters falls in the desired range
            if num_letters in range(5, 9):
                response_json = json.dumps(
                    startGame(num_letters, user_id, game_mode))
                print(response_json)
                return {'statusCode': 201, 'body': response_json}
            return {'statusCode': 400, 'body': 'Invalid word length'}

        # Takes the game_id and returns the status of the game
        if httpMethod == getMethod and event['resource'] == '/games/{game_id}' and 'game_id' in event['pathParameters']:
            game_id = event['pathParameters']['game_id']
            response = table.get_item(Key={'game_id': game_id})
            if 'Item' in response:
                response_body = getGame(response)
                response_json = json.dumps(response_body)
                print(response_json)
                return {'statusCode': 200, 'body': response_json}

            return {'statusCode': 404, 'body': 'Game not found'}

        # Takes the game_id, guessed_word and returns the result based on the guessed_word
        if event['resource'] == '/games/{game_id}/guess' and 'game_id' in event['pathParameters'] :
            game_id = event['pathParameters']['game_id']
            print(game_id)
            guessed_word = (json.loads(event['body'])['guess']).lower()
            response = table.get_item(Key={'game_id': game_id})

            if 'Item' in response:
                game_data = response['Item']['game_data']
                print(game_data)
                
                #Checking if it satisfies base conditions 
                if not guessed_word.isalpha() or len(guessed_word) != len(game_data['word']):
                    return {'statusCode': 400, 'body': 'Invalid guessed word'}
                elif game_data['remaining_turns'] == 0:
                    return {'statusCode': 400, 'body': 'Game over'}
                
                #Checking if the word is vaild using PyDictionary
                elif not dictionary.meaning(guessed_word):
                    return {'statusCode': 400, 'body': 'Invalid guessed word'}
                
                #Checking if the word is plural
                elif dictionary.meaning(guessed_word) and not engine.singular_noun(guessed_word) :
                    return {'statusCode': 400, 'body': 'Error : plural word'}
                
                
                
                
                #Passes all the base condition
                response_body = saveGuess(game_data, guessed_word, game_id)
                response_json = json.dumps(response_body)
                return {'statusCode': 200, 'body': response_json}
            return {'statusCode': 404, 'body': 'Game not found'}

        # Return a 404 error for any other request
        return {'statusCode': 404, 'body': {'message': 'Resource not found'}}
    
    except Exception as e:
        # Log the error message
        print(f'Error: {str(e)}')
        # Return a 500 error with the error message
        return {'statusCode': 500, 'body': {'message': 'Internal server error'}}


#Function used to start a new game
def startGame(num_letters, user_id,mode):
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
        'guesses': [],
        'game_mode':mode
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
        'guesses': game_data['guesses'],
        'mode': game_data['game_mode']
    }
    return {'game_data': response_body}

#Function used to check the guessed word and returns the feedback
def saveGuess(game_data, guess, game_id):
    # Check if the guessed word is the same as the target word
    target_word = game_data['word']
    if guess == target_word:
        # If the guessed word is the same as the target word, mark it as correct
        feedback = 'correct'
    else:
        if game_data['game_mode'] != 'hard':
        # Otherwise, mark each letter in the guessed word as either green, yellow, or gray
            feedback = []
            for i in range(len(guess)):
                if guess[i] == target_word[i]:
                    feedback.append('green')
                elif guess[i] in target_word:
                    feedback.append('yellow')
                else:
                    feedback.append('gray')
        else:
            feedback = None
        


    # Add the guessed word to the list of guesses and decrement the remaining turns
    game_data['guesses'].append(guess)
    game_data['remaining_turns'] -= 1

    # Update the game data in DynamoDB
    table.update_item(Key={'game_id': game_id}, UpdateExpression='SET game_data = :game_data',
                      ExpressionAttributeValues={':game_data': game_data})

    # Return the feedback for the guessed word
    return {'feedback': feedback}
