
## Webhook Endpoint
WhatsApp webhook payload will be forwarded to following endpoint via POST method
```

Example Webhook Response

{
    "contact": {
        "status": "existing/updated/new",
        "phone_number": "XXXXXXXXXX",
        "uid": "XXXXXXXXXX",
        "first_name": "XXXXXXXXXX",
        "last_name": "XXXXXXXXXX",
        "email": "XXXXXX@XXXXXXXXXX.com",
        "language_code": "en",
        "country": "XXXX"
    },
      "message": {
        "whatsapp_business_phone_number_id": "XXXXXXXXXX",
        "whatsapp_message_id": "wamid.XXXXXXXXXX",
        "replied_to_whatsapp_message_id": "wamid.XXXXXXXXXX",
        "is_new_message": true,
        "body": null,
        "status": null,
        "media": {
          "type": "image",
          "link": "link to media",
          "caption": null,
          "mime_type": "image/jpeg",
          "file_name": "XXXXXXXXXX",
          "original_filename": "XXXXXXXXXX"
        }
      },
    "whatsapp_webhook_payload": {
        // WhatsApp webhook data
    }
}


```


















## Variables and Parameters


### Contact Related Dynamic Parameters
You are free to use following dynamic variables for parameters excluding phone_number, template_name, template_language, which will get replaced with contact's concerned field value.
{first_name} {last_name} {full_name} {phone_number} {email} {country} {language_code}
Example Parameters

{
    "from_phone_number_id": "phone number id from which you would like to send message, if not provided default one will be used",
    "phone_number": "phone number with country code without prefixing + or 0",
    "template_name" : "your_template_name",
    "template_language" : "en",
    "header_image" : "https://cdn.pixabay.com/photo/2015/01/07/15/51/woman-591576_1280.jpg",
    "header_video" : "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
    "header_document" : "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
    "header_document_name" : "{full_name}",
    "header_field_1" : "{full_name}",
    "location_latitude" : "22.22",
    "location_longitude" : "22.22",
    "location_name" : "Example Name",
    "location_address" : "Example address",
    "field_1" : "{first_name}",
    "field_2" : "{last_name}",
    "field_3" : "{email}",
    "field_4" : "{country}",
    "field_5" : "{language_code}",
    "button_0" : "{full_name}",
    "button_1" : "{phone_number}",
    "copy_code" : "EXAMPLE_CODE"
}
