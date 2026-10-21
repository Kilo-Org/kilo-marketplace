## 🔥 Critical Rules (READ FIRST)
- **ALWAYS** use field IDs (`fldXXX`) not field names in all operations
- **MANDATORY**: Set `fieldKeyType: "id"` for all record operations
- **RECOMMENDED**: Set `typecast: true` for create/update record(s) operations (auto-converts data types)
- **SECURITY**: Only call Teable APIs from server-side code, never from client-side

## 📝 Records API

### Get Single Record
```
GET /table/{tableId}/record/{recordId}?fieldKeyType=id
```

### Get Multiple Records (with pagination/filtering)
```
GET /table/{tableId}/record?fieldKeyType=id&take=100&skip=0
```
**Query Options:**
- `fieldKeyType`: "id" (mandatory)
- `take`: Max 1000 records per request
- `skip`: For pagination
- `filter`: JSON string (see Filter Guide)
- `search`: Text search
- `orderBy`: Sort records
- `viewId`: Filter by view

### Create Records
```json
POST /table/{tableId}/record
{
  "fieldKeyType": "id",
  "typecast": true,
  "records": [
    {
      "fields": {
        "fldXXX": "value"
      }
    }
  ]
}
```

### Update Single Record
```json
PATCH /table/{tableId}/record/{recordId}
{
  "fieldKeyType": "id",
  "typecast": true,
  "record": {
    "fields": {
      "fldXXX": "new value"
    }
  }
}
```

### Update Multiple Records
```json
PATCH /table/{tableId}/record
{
  "fieldKeyType": "id",
  "typecast": true,
  "records": [
    {
      "id": "recXXX",
      "fields": {
        "fldXXX": "new value"
      }
    }
  ]
}
```

### Delete Records
```
DELETE /table/{tableId}/record/{recordId}              // Single
DELETE /table/{tableId}/record?recordIds=recA,recB    // Multiple
```

## 📊 Aggregation / Statistics API

**For any statistics/aggregation requirement, this is the PRIMARY recommended API.**
Use this endpoint instead of fetching records and aggregating them.

### Get Aggregations
```
GET /table/{tableId}/aggregation
```

**Common query parameters:**
- `viewId`: Optional view to base aggregations on (inherits the view's filter/sort)
- `filter`: JSON string filter (same structure as in **Filter Guide** below)
- `groupBy`: JSON string describing group-by fields
- `field`: Object where keys are statistic function names (e.g. `sum`, `count`) and values are arrays of field IDs to aggregate

**`field` parameter example:**
```json
{
  "field": {
    "sum": ["fldAmount", "fldTax"],
    "average": ["fldAmount"],
    "count": ["fldStatus"]
  }
}
```

**Response shape (simplified):**
```json
[
  {
    "aggregations": [
      {
        "fieldId": "fldAmount",
        "total": { "value": 123.45, "aggFunc": "sum" },
        "group": {
          "Active": { "value": 100, "aggFunc": "sum" },
          "Closed": { "value": 23.45, "aggFunc": "sum" }
        }
      }
    ]
  }
]
```

- Supported statistic functions include: `count`, `empty`, `filled`, `unique`, `max`, `min`, `sum`, `average`, `checked`, `unChecked`, `percentEmpty`, `percentFilled`, `percentUnique`, `percentChecked`, `percentUnChecked`, `earliestDate`, `latestDate`, `dateRangeOfDays`, `dateRangeOfMonths`, `totalAttachmentSize`.
- **Strongly recommended:** For any statistics/aggregation tasks, always use this endpoint instead of iterating records and computing aggregations manually.

## 🏗️ Fields API

### List All Fields
```
GET /table/{tableId}/field
```

### Get Field Details
```
GET /table/{tableId}/field/{fieldId}
```

### Create Field
```json
POST /table/{tableId}/field
{
  "name": "Field Name",
  "type": "singleLineText",
  "options": {}
}
```

### Update Field (name, description only)
```json
PATCH /table/{tableId}/field/{fieldId}
{
  "name": "New Name"
}
```

### Convert Field Type
```json
PUT /table/{tableId}/field/{fieldId}/convert
{
  "type": "number",
  "options": {}
}
```

## 📎 Upload Attachments

The value of an attachment field is an **array**. Each item is an attachment object with at minimum:

```json
{
  "name": "file-name.png",
  "token": "attXXXXXXXX"
}
```

### New record: upload attachment first, then create record

For **new records with attachments**, the upload flow is **three steps**:

1. **Get upload signature** – ask Teable where and how to upload the file
2. **Upload file to storage** – stream the binary to the returned URL
3. **Notify Teable** – finalize the attachment and get metadata (including the token)

#### Step 1 – Get upload signature

```http
POST /attachments/signature
Content-Type: application/json
```

**Body:**

```json
{
  "contentType": "image/png",
  "contentLength": 12345,
  "type": 1,
  "baseId": "bsexxxxx"
}
```

- `contentType`: Mime type of the file (e.g. `image/png`)
- `contentLength`: File size in bytes
- `type`: Upload type (e.g. `1` for table attachments)
- `baseId` (optional): Project ID, when relevant to the upload type

**Response:**

```json
{
  "url": "https://upload-endpoint",
  "uploadMethod": "PUT",
  "token": "attUploadToken",
  "requestHeaders": {
    "Content-Type": "image/png"
  }
}
```

#### Step 2 – Upload file to storage

Use the returned `url`, `uploadMethod` and `requestHeaders` to upload the binary file **directly to storage**:

```javascript
const file = fileBlob; // Browser/File instance or Node.js stream

const { url, uploadMethod, token, requestHeaders } = signature;
delete requestHeaders['Content-Length']; // will be set automatically

await axios(url, {
  method: uploadMethod,
  data: file,
  headers: {
    ...requestHeaders,
  },
});
```

#### Step 3 – Notify Teable and get attachment info

After the file is uploaded, call **notify** to finalize the attachment and get metadata:

```http
POST /attachments/notify/{token}?filename=file-name.png
Content-Type: application/json
```

**Path parameter:**
- `token`: The upload token returned by `/attachments/signature`

**Query:**
- `filename`: Original file name (used as display name and for download)

**Response (simplified):**

```json
{
  "token": "attTokenxxxxx",
  "size": 12345,
  "mimetype": "image/png",
  "path": "/table/xxx",
  "presignedUrl": "https://public-preview-url"
}
```

You can use `filename` as the attachment `name`, and `token` from the response as the attachment `token` when writing to an attachment field.

### New vs update flows

#### 1. Create record with attachment

For **new records with attachments**, first go through the **signature → upload → notify** flow above to get the `name` (your filename) and `token`, then use them in record creation:

```http
POST /table/{tableId}/record
Content-Type: application/json
```

```json
{
  "fieldKeyType": "id",
  "typecast": true,
  "records": [
    {
      "fields": {
        "fldAttachment": [
          {
            "name": "file-name.png",
            "token": "attTokenxxxxx"
          }
        ]
      }
    }
  ]
}
```

#### 2. Update existing record's attachment field

For **updating** an existing record's attachment field, call `uploadAttachment` directly (no need to call `/attachments/signature` or `/attachments/notify` yourself – the API handles the flow internally).

**Option A (recommended): Upload and auto-append to record**

```http
POST /table/{tableId}/record/{recordId}/{fieldId}/uploadAttachment
Content-Type: multipart/form-data
```

**Form fields:**
- `file`: File to upload (binary), OR
- `fileUrl`: Public URL of the file to download and upload (string)

This will **append** the new attachment to the existing attachments in that cell.

**Option B: Manual control (add/remove/reorder)**

1. Fetch record: `GET /table/{tableId}/record/{recordId}?fieldKeyType=id`
2. Modify the attachment array in code (add/remove items)
3. Update record:

```http
PATCH /table/{tableId}/record/{recordId}
Content-Type: application/json
```

```json
{
  "fieldKeyType": "id",
  "typecast": true,
  "record": {
    "fields": {
      "fldAttachment": [
        { "name": "file-1.png", "token": "attToken1" },
        { "name": "file-2.png", "token": "attToken2" }
      ]
    }
  }
}
```

## 🔍 Filter Guide

**Structure:**
```json
{
  "conjunction": "and",
  "filterSet": [
    {
      "fieldId": "fldXXX",
      "operator": "contains",
      "value": "search term"
    }
  ]
}
```

**Operators by Field Type:**
- **Text**: `contains`, `is`, `isNot`, `isEmpty`, `isNotEmpty`
- **Number**: `is`, `isGreater`, `isLess`, `isGreaterEqual`, `isLessEqual`
- **Date**: `isBefore`, `isAfter`, `isOnOrBefore`, `isOnOrAfter`, `isWithIn`
- **Select**: `isAnyOf`, `isNoneOf`, `hasAnyOf`, `hasAllOf`
- **Boolean**: `is`, `isNot`

**Examples:**
```javascript
// Simple filter
const filter = {
  "conjunction": "and",
  "filterSet": [
    {"fieldId": "fldName", "operator": "contains", "value": "John"}
  ]
};

// Complex filter with multiple conditions
const complexFilter = {
  "conjunction": "and",
  "filterSet": [
    {"fieldId": "fldName", "operator": "contains", "value": "John"},
    {
      "conjunction": "or",
      "filterSet": [
        {"fieldId": "fldAge", "operator": "isGreater", "value": 25},
        {"fieldId": "fldStatus", "operator": "is", "value": "Active"}
      ]
    }
  ]
};

// Date filter (last 7 days)
const dateFilter = {
  "conjunction": "and",
  "filterSet": [
    {
      "fieldId": "fldCreated",
      "operator": "isWithIn",
      "value": {
        "mode": "daysAgo",
        "numberOfDays": 7,
        "timeZone": "Asia/Shanghai"
      }
    }
  ]
};

// Use in URL (must stringify)
const url = `/table/tblXXX/record?filter=${encodeURIComponent(JSON.stringify(filter))}`;
```

## 📋 Field Value Types

### When Creating/Updating Records:

```javascript
// Example record with all field types
const record = {
  "fieldKeyType": "id",
  "typecast": true,
  "records": [{
    "fields": {
      // Text fields
      "fldSingleText": "Single line text",
      "fldLongText": "Multi-line\ntext content",

      // Number & boolean
      "fldNumber": 123.45,
      "fldCheckbox": true,
      "fldRating": 4, // 0 to field.options.max (1-10)

      // Select fields
      "fldSingleSelect": "Option1",
      "fldMultiSelect": ["Option1", "Option2"],

      // Date
      "fldDate": "2023-12-25T10:30:00.000Z", // ISO string

      // User & links
      "fldUser": ["usrXXX", "usrYYY"],
      "fldLink": ["recXXX", "recYYY"],

      // Attachments (array of objects)
      "fldAttachment": [{
        "id": "attXXXXXXXXXXXX",
        "name": "file.pdf",
        "path": "/uploads/file.pdf",
        "token": "tokenString",
        "size": 1024,
        "mimetype": "application/pdf"
      }]
    }
  }]
};
```

**💡 Pro Tips:**
- Fields with `isMultipleCellValue: true` accept arrays even for single values
- Use `typecast: true` to let API auto-convert data types
- Don't set computed fields (formula, rollup, autoNumber, createdTime, etc.)

### When Reading Records:

GET responses return expanded objects for user/link fields:

```json
{
  "id": "recXXX",
  "fields": {
    "fldUser": [{
      "id": "usrXXX",
      "title": "John Doe",
      "email": "john@example.com",
      "avatar": "https://example.com/avatar.jpg"
    }],
    "fldLink": [{
      "id": "recXXX",
      "title": "Linked Record Name"
    }],
    "fldAttachment": [{
      "id": "attXXX",
      "name": "file.jpg",
      "url": "https://example.com/file.jpg",
      "size": 1024,
      "type": "image/jpeg",
      "width": 800,
      "height": 600,
      "smThumbnailUrl": "https://example.com/thumb-sm.jpg",
      "lgThumbnailUrl": "https://example.com/thumb-lg.jpg"
    }]
  },
  "autoNumber": 1,
  "createdTime": "2023-12-01T10:00:00.000Z",
  "lastModifiedTime": "2023-12-25T15:30:00.000Z"
}
```

## 🎯 Field Types Reference

**Available Types:**
`singleLineText`, `longText`, `number`, `checkbox`, `singleSelect`, `multipleSelect`, `date`, `user`, `attachment`, `rating`, `link`, `formula`, `rollup`, `autoNumber`, `createdTime`, `lastModifiedTime`, `createdBy`, `lastModifiedBy`, `button`

**Field Object Structure:**
```json
{
  "id": "fldXXX",
  "name": "Field Name",
  "type": "singleSelect",
  "options": {}, // Type-specific configuration
  "cellValueType": "string|number|boolean|dateTime",
  "isMultipleCellValue": false, // true = accepts arrays
  "isComputed": false, // true = read-only (formula, rollup, etc.)
  "notNull": false,
  "isPrimary": false
}
```

## ⚡ Quick Examples

### Basic CRUD Operations:
```javascript
// Create a record
const createResponse = await fetch('/table/tblXXX/record', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    fieldKeyType: 'id',
    typecast: true,
    records: [{
      fields: {
        fldName: 'John Doe',
        fldEmail: 'john@example.com'
      }
    }]
  })
});

// Get records with filter
const getResponse = await fetch(
  '/table/tblXXX/record?' + new URLSearchParams({
    fieldKeyType: 'id',
    filter: JSON.stringify({
      conjunction: 'and',
      filterSet: [
        { fieldId: 'fldName', operator: 'contains', value: 'John' }
      ]
    })
  })
);

// Update record
const updateResponse = await fetch('/table/tblXXX/record/recXXX', {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    fieldKeyType: 'id',
    typecast: true,
    record: {
      fields: {
        fldName: 'John Smith'
      }
    }
  })
});
```

**🚨 Remember:** Always use field IDs (fldXXX) and set fieldKeyType: "id"!
