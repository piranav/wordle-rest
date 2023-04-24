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


### POST /games

Creates a new game with the specified parameters:

- `num_letters`: number of letters in the target word (between 5 and 8)
- `user_id`: unique user ID for the game
- `game_mode`: game mode, either "easy" or "hard"

Example request body:

```
{
  "num_letters": 6,
  "user_id": "abc123",
  "game_mode": "easy"
}
```

Example response body:

```
{
  "game_id": "123456"
}
```

### GET /games/{game_id}

Retrieves the status of the game with the specified ID.

Example response body:

```
{
  "game_id": "123456",
  "num_letters": 6,
  "remaining_turns": 4,
  "game_mode": "easy",
  "correct_letters": ["a", "c"],
  "guessed_words": ["acacia", "brazil", "calico"]
}
```

### GET /games/{game_id}/{guess}

Makes a guess for the game with the specified ID using the specified word. Returns the result of the guess.

Example response body:

```
{
    "feedback": [
        "yellow",
        "green",
        "green",
        "green",
        "green"
    ],
    "correct_letters": [
        "r",
        "a",
        "t",
        "e",
        "r"
    ],
    "remaining_turns": 2
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.




## Cleanup

To delete the stack from AWS and cleanup all resources, run `cdk destroy`. 

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
