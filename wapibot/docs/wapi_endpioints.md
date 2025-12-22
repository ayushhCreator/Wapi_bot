# API Endpoints Documentation

**Source:** https://documenter.getpostman.com/view/17404097/2sA35D4hpx

**Date Extracted:** December 22, 2025

---

## Table of Contents

1. [Authentication](#authentication)
2. [Base URL](#base-url)
3. [Endpoints](#endpoints)
   - [Send Message](#1-send-message)
   - [Send Media Message](#2-send-media-message)
   - [Send Template Message](#3-send-template-message)
   - [Create Contact](#4-create-contact)
   - [Update Contact](#5-update-contact)
   - [Send Interactive Message](#6-send-interactive-message)
   - [Assign Team Member](#7-assign-team-member)
   - [Send Carousel Template Message](#8-send-carousel-template-message)
   - [Get Contact](#9-get-contact)
   - [Get Contacts](#10-get-contacts)

---

## Authentication

All API endpoints require Bearer Token authentication.

**Authorization Header:**
```
Authorization: Bearer {{bearerToken}}
```

---

## Base URL

```
{{apiBaseUrl}}/{{vendorUid}}
```

**Variables:**
- `apiBaseUrl`: Base API URL (e.g., `https://api.example.com`)
- `vendorUid`: Your vendor unique identifier

---

## Endpoints

### 1. Send Message

Send a text message to a contact.

**Endpoint:** `POST /contact/send-message`

**Full URL:** `{{apiBaseUrl}}/{{vendorUid}}/contact/send-message`

#### Request Headers

```
Content-Type: application/json
Authorization: Bearer {{bearerToken}}
```

#### Request Body

```json
{
    "from_phone_number_id": "{{fromPhoneNumberId}}",
    "phone_number": "{{phoneNumber}}",
    "message_body": "your message body",
    "contact": {
        "first_name": "Johan",
        "last_name": "Doe",
        "email": "johndoe@domain.com",
        "country": "india",
        "language_code": "en",
        "groups": "examplegroup1,examplegroup2",
        "custom_fields": {
            "BDay": "2025-09-04"
        }
    }
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from_phone_number_id` | string | No | Phone number ID. If not provided, uses default phone number ID |
| `phone_number` | string | Yes | Recipient phone number |
| `message_body` | string | Yes | Message text content |
| `contact` | object | No | Contact object to create if it doesn't exist |
| `contact.first_name` | string | No | Contact's first name |
| `contact.last_name` | string | No | Contact's last name |
| `contact.email` | string | No | Contact's email address |
| `contact.country` | string | No | Country |
| `contact.language_code` | string | No | Language code (e.g., "en") |
| `contact.groups` | string | No | Comma-separated group names |
| `contact.custom_fields` | object | No | Custom field key-value pairs |

#### Example Request (cURL)

```bash
curl --location '{{apiBaseUrl}}/{{vendorUid}}/contact/send-message' \
--header 'Authorization: Bearer {{bearerToken}}' \
--header 'Content-Type: application/json' \
--data '{
    "from_phone_number_id": "{{fromPhoneNumberId}}",
    "phone_number": "{{phoneNumber}}",
    "message_body": "your message body",
    "contact": {
        "first_name": "Johan",
        "last_name": "Doe",
        "email": "johndoe@domain.com",
        "country": "india",
        "language_code": "en",
        "groups": "examplegroup1,examplegroup2",
        "custom_fields": {
            "BDay": "2025-09-04"
        }
    }
}'
```

#### Response

**Status Code:** 200 OK

```
No response body
```

---

### 2. Send Media Message

Send media content (image, video, document) to a contact.

**Endpoint:** `POST /contact/send-media-message`

**Full URL:** `{{apiBaseUrl}}/{{vendorUid}}/contact/send-media-message`

#### Request Headers

```
Content-Type: application/json
Authorization: Bearer {{bearerToken}}
```

#### Request Body

```json
{
    "from_phone_number_id": "{{fromPhoneNumberId}}",
    "phone_number": "{{phoneNumber}}",
    "media_type": "document",
    "media_url": "https://images.pexels.com/photos/276267/pexels-photo-276267.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2",
    "caption": "your caption for image or video media types",
    "file_name": "your file name for document",
    "contact": {
        "first_name": "Johan",
        "last_name": "Doe",
        "email": "johndoe@domain.com",
        "country": "india",
        "language_code": "en",
        "groups": "examplegroup1,examplegroup2"
    }
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from_phone_number_id` | string | No | Phone number ID. If not provided, uses default phone number ID |
| `phone_number` | string | Yes | Recipient phone number |
| `media_type` | string | Yes | Type of media: "document", "image", or "video" |
| `media_url` | string | Yes | Public URL of the media file |
| `caption` | string | No | Caption for image or video media types |
| `file_name` | string | No | File name for document media type |
| `contact` | object | No | Contact object to create if it doesn't exist |
| `contact.first_name` | string | No | Contact's first name |
| `contact.last_name` | string | No | Contact's last name |
| `contact.email` | string | No | Contact's email address |
| `contact.country` | string | No | Country |
| `contact.language_code` | string | No | Language code |
| `contact.groups` | string | No | Comma-separated group names |

#### Example Request (cURL)

```bash
curl --location '{{apiBaseUrl}}/{{vendorUid}}/contact/send-media-message' \
--header 'Authorization: Bearer {{bearerToken}}' \
--header 'Content-Type: application/json' \
--data '{
    "from_phone_number_id": "{{fromPhoneNumberId}}",
    "phone_number": "{{phoneNumber}}",
    "media_type": "document",
    "media_url": "https://images.pexels.com/photos/276267/pexels-photo-276267.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2",
    "caption": "your caption for image or video media types",
    "file_name": "your file name for document",
    "contact": {
        "first_name": "Johan",
        "last_name": "Doe",
        "email": "johndoe@domain.com",
        "country": "india",
        "language_code": "en",
        "groups": "examplegroup1,examplegroup2"
    }
}'
```

#### Response

**Status Code:** 200 OK

```
No response body
```

---

### 3. Send Template Message

Send a WhatsApp template message with dynamic content.

**Endpoint:** `POST /contact/send-template-message`

**Full URL:** `{{apiBaseUrl}}/{{vendorUid}}/contact/send-template-message`

#### Request Headers

```
Content-Type: application/json
Authorization: Bearer {{bearerToken}}
```

#### Request Body

```json
{
    "from_phone_number_id": "{{fromPhoneNumberId}}",
    "phone_number": "{{phoneNumber}}",
    "template_name": "your_template_name",
    "template_language": "en",
    "header_image": "https://cdn.pixabay.com/photo/2015/01/07/15/51/woman-591576_1280.jpg",
    "header_video": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
    "header_document": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
    "header_document_name": "{full_name}",
    "header_field_1": "{full_name}",
    "location_latitude": "22.22",
    "location_longitude": "22.22",
    "location_name": "{first_name}",
    "location_address": "{country}",
    "field_1": "{Age}",
    "field_2": "{full_name}",
    "field_3": "{first_name}",
    "field_4": "{last_name}",
    "button_0": "{email}",
    "button_1": "{phone_number}",
    "copy_code": "YourCode",
    "contact": {
        "first_name": "Johan",
        "last_name": "Doe",
        "email": "johndoe@domain.com",
        "country": "india",
        "language_code": "en",
        "groups": "examplegroup1,examplegroup2"
    }
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from_phone_number_id` | string | No | Phone number ID. If not provided, uses default phone number ID |
| `phone_number` | string | Yes | Recipient phone number |
| `template_name` | string | Yes | Name of the WhatsApp template |
| `template_language` | string | Yes | Language code for the template (e.g., "en") |
| `header_image` | string | No | URL for header image |
| `header_video` | string | No | URL for header video |
| `header_document` | string | No | URL for header document |
| `header_document_name` | string | No | Document name with placeholders |
| `header_field_1` | string | No | Header field placeholder value |
| `location_latitude` | string | No | Latitude coordinate for location |
| `location_longitude` | string | No | Longitude coordinate for location |
| `location_name` | string | No | Location name with placeholders |
| `location_address` | string | No | Location address with placeholders |
| `field_1` | string | No | Template body field 1 placeholder value |
| `field_2` | string | No | Template body field 2 placeholder value |
| `field_3` | string | No | Template body field 3 placeholder value |
| `field_4` | string | No | Template body field 4 placeholder value |
| `button_0` | string | No | Button 0 placeholder value |
| `button_1` | string | No | Button 1 placeholder value |
| `copy_code` | string | No | Copy code for quick reply |
| `contact` | object | No | Contact object to create if it doesn't exist |

**Note:** Template placeholders like `{full_name}`, `{first_name}`, `{Age}`, etc., will be replaced with actual contact field values.

#### Example Request (cURL)

```bash
curl --location '{{apiBaseUrl}}/{{vendorUid}}/contact/send-template-message' \
--header 'Authorization: Bearer {{bearerToken}}' \
--header 'Content-Type: application/json' \
--data '{
    "from_phone_number_id": "{{fromPhoneNumberId}}",
    "phone_number": "{{phoneNumber}}",
    "template_name": "your_template_name",
    "template_language": "en",
    "header_image": "https://cdn.pixabay.com/photo/2015/01/07/15/51/woman-591576_1280.jpg",
    "header_video": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
    "header_document": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
    "header_document_name": "{full_name}",
    "header_field_1": "{full_name}",
    "location_latitude": "22.22",
    "location_longitude": "22.22",
    "location_name": "{first_name}",
    "location_address": "{country}",
    "field_1": "{Age}",
    "field_2": "{full_name}",
    "field_3": "{first_name}",
    "field_4": "{last_name}",
    "button_0": "{email}",
    "button_1": "{phone_number}",
    "copy_code": "YourCode",
    "contact": {
        "first_name": "Johan",
        "last_name": "Doe",
        "email": "johndoe@domain.com",
        "country": "india",
        "language_code": "en",
        "groups": "examplegroup1,examplegroup2"
    }
}'
```

#### Response

**Status Code:** 200 OK

```
No response body
```

---

### 4. Create Contact

Create a new contact in the system.

**Endpoint:** `POST /contact/create`

**Full URL:** `{{apiBaseUrl}}/{{vendorUid}}/contact/create`

#### Request Headers

```
Content-Type: application/json
Authorization: Bearer {{bearerToken}}
```

#### Request Body

```json
{
    "phone_number": "{{phoneNumber}}",
    "first_name": "Johan",
    "last_name": "Doe",
    "email": "johndoe@domain.com",
    "country": "india",
    "language_code": "en",
    "groups": "examplegroup1,examplegroup2",
    "custom_fields": {
        "BDay": "2025-09-01"
    }
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `phone_number` | string | Yes | Contact's phone number (unique identifier) |
| `first_name` | string | No | Contact's first name |
| `last_name` | string | No | Contact's last name |
| `email` | string | No | Contact's email address |
| `country` | string | No | Country |
| `language_code` | string | No | Language code (e.g., "en") |
| `groups` | string | No | Comma-separated group names |
| `custom_fields` | object | No | Custom field key-value pairs |

#### Example Request (cURL)

```bash
curl --location '{{apiBaseUrl}}/{{vendorUid}}/contact/create' \
--header 'Authorization: Bearer {{bearerToken}}' \
--header 'Content-Type: application/json' \
--data '{
    "phone_number": "{{phoneNumber}}",
    "first_name": "Johan",
    "last_name": "Doe",
    "email": "johndoe@domain.com",
    "country": "india",
    "language_code": "en",
    "groups": "examplegroup1,examplegroup2",
    "custom_fields": {
        "BDay": "2025-09-01"
    }
}'
```

#### Response

**Status Code:** 200 OK

```
No response body
```

---

### 5. Update Contact

Update an existing contact's information.

**Endpoint:** `POST /contact/update`

**Full URL:** `{{apiBaseUrl}}/{{vendorUid}}/contact/update`

#### Request Headers

```
Content-Type: application/json
Authorization: Bearer {{bearerToken}}
```

#### Request Body

```json
{
    "phone_number": "{{phoneNumber}}",
    "first_name": "Johan",
    "last_name": "Doe",
    "email": "johndoe@domain.com",
    "country": "india",
    "language_code": "en",
    "groups": "examplegroup1,examplegroup2",
    "custom_fields": {
        "BDay": "2025-09-01"
    }
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `phone_number` | string | Yes | Contact's phone number (identifier) |
| `first_name` | string | No | Contact's first name |
| `last_name` | string | No | Contact's last name |
| `email` | string | No | Contact's email address |
| `country` | string | No | Country |
| `language_code` | string | No | Language code |
| `groups` | string | No | Comma-separated group names |
| `custom_fields` | object | No | Custom field key-value pairs |

#### Example Request (cURL)

```bash
curl --location '{{apiBaseUrl}}/{{vendorUid}}/contact/update' \
--header 'Authorization: Bearer {{bearerToken}}' \
--header 'Content-Type: application/json' \
--data '{
    "phone_number": "{{phoneNumber}}",
    "first_name": "Johan",
    "last_name": "Doe",
    "email": "johndoe@domain.com",
    "country": "india",
    "language_code": "en",
    "groups": "examplegroup1,examplegroup2",
    "custom_fields": {
        "BDay": "2025-09-01"
    }
}'
```

#### Response

**Status Code:** 200 OK

```
No response body
```

---

### 6. Send Interactive Message

Send interactive messages with buttons or list options.

**Endpoint:** `POST /contact/send-interactive-message`

**Full URL:** `{{apiBaseUrl}}/{{vendorUid}}/contact/send-interactive-message`

#### Request Headers

```
Content-Type: application/json
Authorization: Bearer {{bearerToken}}
```

#### Request Body (Button Example)

```json
{
    "from_phone_number_id": "{{fromPhoneNumberId}}",
    "phone_number": "{{phoneNumber}}",
    "interactive_type": "button",
    "body_text": "Choose an option:",
    "buttons": [
        {
            "id": "button_1",
            "title": "Option 1"
        },
        {
            "id": "button_2",
            "title": "Option 2"
        }
    ]
}
```

#### Request Body (List Example)

```json
{
    "from_phone_number_id": "{{fromPhoneNumberId}}",
    "phone_number": "{{phoneNumber}}",
    "interactive_type": "list",
    "body_text": "Please select from the menu:",
    "button_text": "View Options",
    "sections": [
        {
            "title": "Section 1",
            "rows": [
                {
                    "id": "row_1",
                    "title": "Option 1",
                    "description": "Description for option 1"
                },
                {
                    "id": "row_2",
                    "title": "Option 2",
                    "description": "Description for option 2"
                }
            ]
        }
    ]
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from_phone_number_id` | string | No | Phone number ID |
| `phone_number` | string | Yes | Recipient phone number |
| `interactive_type` | string | Yes | Type: "button" or "list" |
| `body_text` | string | Yes | Message body text |
| `buttons` | array | Conditional | Required for button type (max 3 buttons) |
| `button_text` | string | Conditional | Required for list type |
| `sections` | array | Conditional | Required for list type |

**Note:** Complete request/response examples were not available in the extracted documentation. Please refer to the official documentation for detailed examples.

---

### 7. Assign Team Member

Assign a team member to a conversation.

**Endpoint:** `POST /conversation/assign-team-member`

**Full URL:** `{{apiBaseUrl}}/{{vendorUid}}/conversation/assign-team-member`

#### Request Headers

```
Content-Type: application/json
Authorization: Bearer {{bearerToken}}
```

#### Request Body (Expected)

```json
{
    "conversation_id": "{{conversationId}}",
    "team_member_id": "{{teamMemberId}}"
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `conversation_id` | string | Yes | ID of the conversation |
| `team_member_id` | string | Yes | ID of the team member to assign |

**Note:** Complete request/response examples were not available in the extracted documentation. Please refer to the official documentation for detailed examples.

---

### 8. Send Carousel Template Message

Send a carousel template message with multiple cards.

**Endpoint:** `POST /contact/send-carousel-template-message`

**Full URL:** `{{apiBaseUrl}}/{{vendorUid}}/contact/send-carousel-template-message`

#### Request Headers

```
Content-Type: application/json
Authorization: Bearer {{bearerToken}}
```

#### Request Body (Expected)

```json
{
    "from_phone_number_id": "{{fromPhoneNumberId}}",
    "phone_number": "{{phoneNumber}}",
    "template_name": "carousel_template_name",
    "template_language": "en",
    "cards": [
        {
            "card_index": 0,
            "components": []
        },
        {
            "card_index": 1,
            "components": []
        }
    ]
}
```

**Note:** Complete request/response examples were not available in the extracted documentation. Please refer to the official documentation for detailed examples.

---

### 9. Get Contact

Retrieve a single contact's information.

**Endpoint:** `GET /contact`

**Full URL:** `{{apiBaseUrl}}/{{vendorUid}}/contact`

#### Request Headers

```
Authorization: Bearer {{bearerToken}}
```

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `phone_number` | string | Yes | Contact's phone number |

#### Example Request (cURL)

```bash
curl --location '{{apiBaseUrl}}/{{vendorUid}}/contact?phone_number={{phoneNumber}}' \
--header 'Authorization: Bearer {{bearerToken}}'
```

#### Response (Expected)

**Status Code:** 200 OK

```json
{
    "id": "contact_id",
    "phone_number": "1234567890",
    "first_name": "Johan",
    "last_name": "Doe",
    "email": "johndoe@domain.com",
    "country": "india",
    "language_code": "en",
    "groups": ["examplegroup1", "examplegroup2"],
    "custom_fields": {
        "BDay": "2025-09-01"
    },
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-15T00:00:00Z"
}
```

**Note:** Complete response examples were not available in the extracted documentation. Please refer to the official documentation for detailed examples.

---

### 10. Get Contacts

Retrieve a list of all contacts.

**Endpoint:** `GET /contacts`

**Full URL:** `{{apiBaseUrl}}/{{vendorUid}}/contacts`

#### Request Headers

```
Authorization: Bearer {{bearerToken}}
```

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number for pagination (default: 1) |
| `limit` | integer | No | Number of contacts per page (default: 50) |
| `search` | string | No | Search query for filtering contacts |

#### Example Request (cURL)

```bash
curl --location '{{apiBaseUrl}}/{{vendorUid}}/contacts?page=1&limit=50' \
--header 'Authorization: Bearer {{bearerToken}}'
```

#### Response (Expected)

**Status Code:** 200 OK

```json
{
    "data": [
        {
            "id": "contact_id_1",
            "phone_number": "1234567890",
            "first_name": "Johan",
            "last_name": "Doe",
            "email": "johndoe@domain.com",
            "country": "india",
            "language_code": "en"
        },
        {
            "id": "contact_id_2",
            "phone_number": "0987654321",
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "janesmith@domain.com",
            "country": "usa",
            "language_code": "en"
        }
    ],
    "pagination": {
        "current_page": 1,
        "total_pages": 10,
        "total_contacts": 500,
        "limit": 50
    }
}
```

**Note:** Complete response examples were not available in the extracted documentation. Please refer to the official documentation for detailed examples.

---

## Common Response Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid or missing authentication token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

---

## Notes

1. **Authentication:** All endpoints require a valid Bearer token in the Authorization header.
2. **Rate Limiting:** API calls may be subject to rate limiting. Check response headers for rate limit information.
3. **Phone Number Format:** Phone numbers should include country code (e.g., "919876543210" for India).
4. **Contact Auto-Creation:** Several messaging endpoints support automatic contact creation if the contact doesn't exist.
5. **Template Messages:** Template messages must be pre-approved by WhatsApp before use.
6. **Media URLs:** Media URLs must be publicly accessible and hosted on HTTPS.
7. **Placeholders:** Template placeholders use the format `{field_name}` and are replaced with actual contact field values.

---

## Variables Reference

Common variables used in the API:

| Variable | Description | Example |
|----------|-------------|---------|
| `{{apiBaseUrl}}` | Base API URL | `https://api.wapibot.com` |
| `{{vendorUid}}` | Your vendor unique identifier | `vendor_abc123` |
| `{{bearerToken}}` | Your API authentication token | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `{{fromPhoneNumberId}}` | Phone number ID to send from | `phone_123456` |
| `{{phoneNumber}}` | Recipient phone number | `919876543210` |

---

## Additional Resources

- **Official Documentation:** https://documenter.getpostman.com/view/17404097/2sA35D4hpx
- **Support:** Contact your API provider for additional support and documentation

---

**Document Version:** 1.0  
**Last Updated:** December 22, 2025
