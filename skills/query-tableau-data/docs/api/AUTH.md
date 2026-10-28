# Tableau HTTP Authentication

The **VizQL Data Service (VDS)** used to query data sources is part of a broader set of HTTP APIs available to users on both Tableau Cloud and Server. It uses the same authentication mechanisms as the other REST API methods.

All Tableau HTTP API endpoints require an authentication token in the `X-Tableau-Auth` header of each request. The token lets Tableau Cloud or Tableau Server verify your identity and provide access to resources according to your permissions.

To get an authentication token, you must call the Tableau REST API `Sign In` method, in one of three ways:

1. Personal Access Token (`PAT`)
2. Username & password
3. Connected Apps (`JWT`)

This skill preferences `PAT` since it is easy for users to obtain from their Tableau account page. The `JWT` option is designed for secure server environments and requires site admin access. Username and password should only be used as an exception.


## Managing Credentials

This inevitably requires secure credential management. You will need to create a `.env` file to store environment variables.

Place the `.env` file in the skill root directory, next to `.env.template` and `pyproject.toml`. You can find the template at [.env.template](../../.env.template) — copy it and fill in your values.

The [query_tableau_data_py](../../src/query_tableau_data_py) package manages secure access to environment variables and all of the basic components to query data from Tableau securely.


## Permissions

When you sign in with any of the supported authentication methods you must use the redemeed token for all subsequent operations via HTTP. As a result, all responses you get from Tableau moving forward enforce the individual and group permissions configured for those user credentials. Querying data sources is an action that both regular users and Tableau site admins can perform.

> _NOTE_: Published datasources require the API Access permission enabled. This can be done manually via the permissions dialog UI or via the REST API.

---

## Sign In

METHOD: `POST /api/api-version/auth/signin`

> _Note_: For Tableau Cloud, the server address in the URI must contain the pod name, such as prod-ca-a or us-east-1. For example, the URI to sign in to a site in the 10ay pod would be:https://prod-ca-a.online.tableau.com/api/api-version/auth/signin

_Example Sign-In Request_:
```bash
curl "https://{my-server}/api/{api-version}/auth/signin" -X POST -d @signin.json
```

### Personal Access Token (PAT)

REQUEST PAYLOAD:
```json
{
    "credentials": {
        "personalAccessTokenName": "personal-access-token-name",
        "personalAccessTokenSecret": "personal-access-token-secret",
        "site": {
            "contentUrl": "content-url"
        }
    }
}
```

### Username & Password

REQUEST PAYLOAD:
```json
{
    "credentials": {
        "name": "username",
        "password": "password",
        "site": {
            "contentUrl": "content-url"
        }
    }
}
```

### Credentials

All authentication methods return a credentials response:

RESPONSE PAYLOAD:
```json
{
    "credentials": {
        "token": "authentication-token",
        "estimatedTimeToExpiration": "time-to-expiration",
        "site": {
            "id": "site-id",
            "contentUrl": "content-url"
        },
        "user": {
            "id": "user-id-of-signed-in-user"
        }
    }
}
```

When you get the response, you parse useful values such as the credentials token out of the response and use them in the [query_tableau_data_py](../../src/query_tableau_data_py) package.

By default, the credentials token is good for **240 minutes**. If your application needs to be able to make additional calls after the credentials token has expired, you can call Sign In again and get a new credentials token.

You include the credentials token as the value of the `X-Tableau-Auth` header for all other REST API calls.

_Example Authenticated Request_:
```bash
curl "https://{my-server}/api/{api-version}/sites/{site-id}/{method}" -X GET -H "X-Tableau-Auth: ${TABLEAU_CREDENTIALS_TOKEN:?required}"
```

When you are finished with a session, you call `Sign Out`. This invalidates the credentials token, which makes sure that no one else can use the credentials token to make calls to the REST API.

> _Note_: The credentials token is valid for REST API calls, VizQL Data Service calls, and Tableau Metadata API (GraphQL) queries. You cannot use the credentials token as authentication for other operations with Tableau Server or Tableau Cloud. In addition, the credentials token is good only for operations in the site that you're signed in to. You cannot sign in to one site and then use the token you get back to send requests to a different site. If you do, the server returns an `HTTP 403` (Forbidden) error.
