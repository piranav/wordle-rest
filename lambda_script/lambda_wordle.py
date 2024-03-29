import boto3
import simplejson as json
import random
import string
import urllib.request

#Dynamo Table
dynamodbTableName = 'wordle_data'
# Defining the dynamo cliet
dynamodb = boto3.resource('dynamodb')
# getting the table
table = dynamodb.Table(dynamodbTableName)

# Example data containing all valid words
url = "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"
response = urllib.request.urlopen(url)
valid_words= response.read().decode().split("\n")
valid_words = [word.rstrip() for word in valid_words]


def lambda_handler(event, context):
    try:
        
        #HTTP REQUESTS
        # Extracting the http method
        httpMethod = event['httpMethod']
        getMethod = 'GET'
        postMethod = 'POST'
        
        # Takes the number of letters, user_id and game_mode, creates a new game, returns the game id
        if httpMethod == postMethod and event['resource'] == '/games':
            num_letters = int(json.loads(event['body'])['num_letters'])
            user_id = json.loads(event['body'])['user_id']
            game_mode = json.loads(event['body'])['game_mode']
        
            # Checking if the number of letters falls in the desired range
            if num_letters in range(5, 9):
                response_json = json.dumps(
                    startGame(num_letters, user_id, game_mode))
                return {'statusCode': 200, 'body': response_json}
            
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

        # Takes the guessed_word and returns the result based on the guessed_word
        if event['resource'] == '/games/{game_id}/{guess}' and 'game_id' in event['pathParameters'] and 'guess' in event['pathParameters'] :
            game_id = event['pathParameters']['game_id']
            guessed_word = event['pathParameters']['guess']
            response = table.get_item(Key={'game_id': game_id})

            if 'Item' in response:
                game_data = response['Item']['game_data']
            
                #Checking if it satisfies base conditions 
                if not guessed_word.isalpha() or len(guessed_word) != len(game_data['word']):
                    return {'statusCode': 400, 'body': 'Invalid guessed word'}
                elif game_data['remaining_turns'] == 0:
                    if game_data['resut'] != "Won":
                        game_data['result'] = "Lost"
                    return {'statusCode': 400, 'body': 'Game over, Correct word:' + str(game_data['word'])}
                #Checking if the word is valid
                elif guessed_word not in valid_words :
                    return {'statusCode': 400, 'body': 'Error : Not a Valid word'}
                #Checking if the word is a plural word
                elif guessed_word.endswith("s") and guessed_word[:-1] in valid_words:
                    return {'statusCode': 400, 'body': 'Error : Plural word'}
                
                #Hard Mode configuration and if anything other than your first try
                elif game_data['game_mode'].lower() == 'hard' and int(game_data['remaining_turns']) != len(game_data['word'])+1:
                    for letter in game_data['correct_letters']:
                        if letter not in list(guessed_word):
                            return {'statusCode': 400, 'body': 'Error : All the correct letters are not included'}
                
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
        'correct_letters':[],
        'game_mode':mode,
        'result': 'Ongoing'
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
        'correct_letters': game_data['correct_letters'],
        'mode': game_data['game_mode'],
        'Status': game_data['result']
    }
    return {'game_data': response_body}

#Function used to check the guessed word and returns the feedback
def saveGuess(game_data, guess, game_id):
    # Check if the guessed word is the same as the target word
    target_word = game_data['word']
    if guess == target_word:
        # If the guessed word is the same as the target word, mark it as correct
        feedback = 'correct'
        correct_letters = list(guess)
        game_data['result'] = "Won"
    else:
        # Otherwise, mark each letter in the guessed word as either green, yellow, or gray
        feedback = []
        correct_letters = []
        for i in range(len(guess)):
            if guess[i] == target_word[i]:
                feedback.append('green')
                correct_letters.append(guess[i]) 
            elif guess[i] in target_word:
                feedback.append('yellow')
                correct_letters.append(guess[i])
            else:
                feedback.append('gray')

    # Add the guessed word to the list of guesses and decrement the remaining turns
    game_data['guesses'].append(guess)
    game_data['correct_letters'] = correct_letters
    game_data['remaining_turns'] -= 1

    # Update the game data in DynamoDB
    table.update_item(Key={'game_id': game_id}, UpdateExpression='SET game_data = :game_data',
                      ExpressionAttributeValues={':game_data': game_data})

    # Return the feedback for the guessed word
    return {'feedback': feedback, 'correct_letters': correct_letters, 'remaining_turns': game_data['remaining_turns'] }
