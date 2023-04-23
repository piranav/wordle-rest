# Wordle Game REST API

This project creates an AWS infrastructure for a Wordle game REST API using the AWS Cloud Development Kit (CDK) and Python. The REST API allows users to create a game, guess a word in the game, and get the status of the game. 

## Requirements

- AWS account
- Python 3.10
- AWS CLI
- AWS CDK

## Installation

1. Clone the repository: `git clone https://github.com/<username>/<repository-name>.git`
2. Navigate to the project directory: `cd <repository-name>`
3. Install dependencies: `pip install -r requirements.txt`
4. Deploy the stack to AWS: `cdk deploy`

## Usage

The API Gateway endpoint is printed to the console after the stack is deployed. You can make API requests to this endpoint to interact with the Wordle game REST API. 

### Create a Game

To create a new game, send a POST request to the `/games` endpoint with a JSON body that includes the `game_id`:

```
POST /games

{
  "game_id": "abcd1234"
}
```

### Guess a Word

To guess a word in a game, send a POST request to the `/games/{game_id}/guesses` endpoint with a JSON body that includes the `guess`:

```
POST /games/abcd1234/guesses

{
  "guess": "apple"
}
```

### Get Game Status

To get the status of a game, send a GET request to the `/games/{game_id}` endpoint:

```
GET /games/abcd1234
```

## Cleanup

To delete the stack from AWS and cleanup all resources, run `cdk destroy`. 

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
