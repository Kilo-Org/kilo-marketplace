# Excel Cube Functions

Cube functions retrieve data from OLAP (Online Analytical Processing) cubes or
Power Pivot data models. They require a connection to an Analysis Services
(SSAS/Azure AS/Power BI) data source.

Source: https://support.microsoft.com/en-us/office/excel-functions-by-category-5f91f4e9-7b42-46d2-9bd1-63f26a86c0eb

---

`CUBEMEMBER(connection, member_expression, [caption])` — Returns a member or tuple from a cube hierarchy; validates that the member or tuple exists in the cube.

`CUBEMEMBERPROPERTY(connection, member_expression, property)` — Returns the value of a member property in a cube; validates member name and returns the specified property.

`CUBERANKEDMEMBER(connection, set_expression, rank, [caption])` — Returns the nth ranked member in a set; useful for top-N lists such as top sales performers.

`CUBESET(connection, set_expression, [caption], [sort_order], [sort_by])` — Defines a calculated set of members or tuples by sending a set expression to the server, then returns that set to Excel.

`CUBESETCOUNT(set)` — Returns the number of items in a set defined by CUBESET.

`CUBEVALUE(connection, member_expression1, [member_expression2], ...)` — Returns an aggregated value from a cube filtered by one or more member expressions.
