## User Functions

## Why use user functions

User functions can be used to create user filters or row-level security filters that affect visualizations published to Tableau Server or Tableau Cloud, so that only certain people can see your visualization.

For example, if you have a visualization that shows the sales performance for each employee in your department published on Tableau Server or Tableau Cloud, you might want to only allow employees to see their own sales numbers when they access that visualization.

In this case, you can use the ISMEMBEROF function to create a field that returns true if the username of the person signed in to the server is a member of a specified group (on the server), such as the "Managers" group, for example. Then when you filter the view using this calculated field, only a person who is part of that group can see the data.

The calculation in this case might look something like the following:

```
ISMEMBEROF('Managers')
```

Note: If your group or user names contain certain non-alphanumeric characters, you must use HTML URL encoding for the special characters when using the functions.

Some special characters are permitted without HTML URL encoding, such as underscores, parentheses, and exclamation points. `_ ( ) !` Many other characters must be encoded.

For example, the function `ISMEMBEROF("USERS+")` needs to be written as `ISMEMBEROF("USERS%2B")`, because the '%2B' is the HTML URL Encoding for the '+' symbol.

---

## User functions available in Tableau

### FULLNAME( )

|  |  |
| --- | --- |
| Syntax | `FULLNAME( )` |
| Output | String |
| Definition | Returns the full name for the current user. |
| Example | ``` FULLNAME( ) ```   This returns the full name of the signed in user, such as "Hamlin Myrer".   ``` [Manager] = FULLNAME( ) ```   If manager "Hamlin Myrer" is signed in, this example returns TRUE only if the Manager field in the view contains "Hamlin Myrer". |
| Notes | This function checks:   * Tableau Cloud and Tableau Server: the full name of the signed-in user * Tableau Desktop: the local or network full name for the user   **User filters**  When used as a filter, a calculated field such as `[Username field] = FULLNAME( )` can be used to create a user filter that only shows data that is relevant to the person signed in to the server. |

### ISFULLNAME

|  |  |
| --- | --- |
| Syntax | `ISFULLNAME("User Full Name")` |
| Output | Boolean |
| Definition | Returns `TRUE` if the current user's full name matches the specified full name or `FALSE` if it does not match. |
| Example | ``` ISFULLNAME("Hamlin Myrer") ``` |
| Notes | The `<"User Full Name">` argument must be a literal string, not a field.  This function checks:   * Tableau Cloud and Tableau Server: the full name of the signed-in user * Tableau Desktop: the local or network full name for the user |

### ISMEMBEROF

|  |  |
| --- | --- |
| Syntax | `ISMEMBEROF("Group Name")` |
| Output | Boolean or null |
| Definition | Returns `TRUE` if the person currently using Tableau is a member of a group that matches the given string, `FALSE` if they're not a member, and `NULL` if they're not signed in. |
| Example | ``` ISMEMBEROF('Superstars') ```  ``` ISMEMBEROF('domain.lan\Sales') ``` |
| Notes | The `<"Group Full Name">` argument must be a literal string, not a field.  If the user is signed in to Tableau Cloud or Tableau Server, group membership is determined by Tableau groups. The function will return TRUE if the given string is "All Users"  The `ISMEMBEROF( )` function will also accept Active Directory domains. The Active Directory domain must be declared in the calculation with the group name.  If a change is made to a user's group membership, the change in the data that is based on the group membership is reflected in a workbook or view with a new session. The existing session will reflect stale data. |

### ISUSERNAME

|  |  |
| --- | --- |
| Syntax | `ISUSERNAME("username")` |
| Output | Boolean |
| Definition | Returns `TRUE` if the current user's username matches the specified username or `FALSE` if it does not match. |
| Example | ``` ISUSERNAME("hmyrer") ``` |
| Notes | The `<"username">` argument must be a literal string, not a field.  This function checks:   * Tableau Cloud and Tableau Server: the username of the signed-in user * Tableau Desktop: the local or network username for the user |

### USERDOMAIN( )

|  |  |
| --- | --- |
| Syntax | `USERDOMAIN( )` |
| Output | String |
| Definition | Returns the domain for the current user . |
| Notes | This function checks:   * Tableau Cloud and Tableau Server: the user domain of the signed-in user * Tableau Desktop: the local domain if the user is on a domain |

### USERNAME( )

|  |  |
| --- | --- |
| Syntax | `USERNAME( )` |
| Output | String |
| Definition | Returns the username for the current user. |
| Example | ``` USERNAME( ) ```   This returns the username of the signed in user, such as "hmyrer".   ``` [Manager] = USERNAME( ) ```   If manager "hmyrer" is signed in, this example returns TRUE only if the Manager field in the view contains "hmyrer". |
| Notes | This function checks:   * Tableau Cloud and Tableau Server: the username of the signed-in user * Tableau Desktop: the local or network username for the user   **User filters**  When used as a filter, a calculated field such as `[Username field] = USERNAME( )` can be used to create a user filter that only shows data that is relevant to the person signed in to the server. |

### USERATTRIBUTE

**Note**: Before using this function, see User attribute functions to control and customize data access. For more information, depending on your workflow, see Authentication and Embedded Views(Link opens in a new window) in the Embedding API v3 Help, OIDC(Link opens in a new window) or SAML(Link opens in a new window) topics.

|  |  |
| --- | --- |
| Syntax | `USERATTRIBUTE('attribute_name')` |
| Output | String or null |
| Definition | If `<'attribute_name'>` is part of the JWT (via connected apps, UAT, OIDC claim) or SAML XML response passed to Tableau, the calculation returns the first value of `<'attribute_name'>`.  Returns null if `<'attribute_name'>` does not exist. |
| Example | Suppose "Region" is the user attribute included in the JWT or SAML response and passed to Tableau.  As the workbook author, you can set up your visualization to filter data based on a specified region. In that filter, you can reference the following calculation.   ``` [Region] = USERATTRIBUTE("Region") ```   When User2 from the West region views the embedded visualization, Tableau shows the appropriate data for the West region only. |
| Notes | You can use the `USERATTRIBUTEINCLUDES` function if you expect `<'attribute_name'>` to return multiple values. |

### USERATTRIBUTEINCLUDES

**Note**: Before using this function, see User attribute functions to control and customize data access. For more information, depending on your workflow, see Authentication and Embedded Views(Link opens in a new window) in the Embedding API v3 Help, OIDC(Link opens in a new window) or SAML(Link opens in a new window) topics.

|  |  |
| --- | --- |
| Syntax | `USERATTRIBUTEINCLUDES('attribute_name', 'expected_value')` |
| Output | Boolean |
| Definition | Returns `TRUE` if both of the following are true:   * `<'attribute_name'>` is part of the JWT (via connected app, UAT, OIDC claim) or SAML XML response passed to Tableau * one of `<'attribute_name'>` values equals `<'expected_value'>` .   Returns `FALSE` otherwise. |
| Example | Suppose "Region" is the user attribute included in the JWT or SAML response and passed to Tableau.  As the workbook author, you can set up your visualization to filter data based on a specified region. In that filter, you can reference the following calculation.   ``` USERATTRIBUTEINCLUDES('Region', [Region]) ```   If User2 from the West region accesses the embedded visualization, Tableau checks if the Region user attribute matches one of [Region] field values. When true, the visualization shows the appropriate data.  When User3 from the North region accesses the same visualization, she’s unable to see any data because there’s no match with [Region] field values. |
