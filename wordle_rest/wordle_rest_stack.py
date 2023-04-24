from aws_cdk import (
    Stack,
    aws_lambda,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_iam as iam
)
from constructs import Construct

class WordleRestStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #Creating an iam role with access to cloudwatch and dynamodb
        wordle_lambda_role = iam.Role(self, "wordle_lambda_role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            role_name = "wordle_lambda")
        
        wordle_lambda_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"))
        wordle_lambda_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchFullAccess"))
        wordle_lambda_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess"))
     
        #Creating the aws lambda function for the api.
        wordle_lambda_function = aws_lambda.Function(self,
                                                     'wordle_lambda_function',
                                                     code = aws_lambda.Code.from_asset("./lambda_script/"),
                                                     handler = "lambda_wordle.lambda_handler",
                                                     role=wordle_lambda_role,
                                                     runtime = aws_lambda.Runtime.PYTHON_3_10,
                                                     function_name = 'wordle_lambda')


        #Creating the DynamoDB table
        game_table = dynamodb.Table(self, "WordleData",
        table_name= 'wordle_data',
        partition_key=dynamodb.Attribute(name="game_id", type=dynamodb.AttributeType.STRING),
        billing_mode=dynamodb.BillingMode.PROVISIONED
        )
        
        #Creating the API Gateway
        rest_api = apigateway.RestApi(self, "WordleRestApi",
                  rest_api_name="wordle_rest_api",
                  description="Wordle Game REST API",
                  endpoint_types=[apigateway.EndpointType.REGIONAL])
            
        # creating a games resource and method in the REST API
        games_resource = rest_api.root.add_resource('games')
        
        wordle_integration = apigateway.LambdaIntegration(wordle_lambda_function)


        #add a POST method to the games resource
        games_method = games_resource.add_method("POST", wordle_integration)

        # creating games/{game_id} resource and method in the REST API
        game_id_resource = games_resource.add_resource('{game_id}')

        game_id_method = game_id_resource.add_method("GET", wordle_integration)

        # Creating games/{game_id}/guesses
        guesses_resource = game_id_resource.add_resource('{guess}')
        guesses_method = guesses_resource.add_method('PUT',wordle_integration)

        