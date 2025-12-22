# User Story

---

## Introduction

I'm Creating this chatbot to interact with user to book services (One time and Subscription).

In this chatbot flow  we will handle these cases,defined below :

1. Customer Information (First_name,Last_name) First_name and  last_name can be sent by the customer in single chat or two subsequent chats in a session.

2. Customer Requirement [wants a new service ,wants one -time booking or subscription , wants to do Rescheduling of their booked  service, or Enquiry about services,wants to file complaint,wants to know about service updates(exisitng customer),Wants to pay /submit proof of payment ,wants to know new offers]

3. We might be handling the same customer for totally different bookings. Either of the bookings can be incomplete. 

4. I have already made endpoints from our webapp connecting it with this chatbot for fetching and posting data from our ERP systems.

5. The system has to be senstive and dynamic enough to detect the stages of convestion  and steer the converstion to enable a successful conversion with of user.

6. The sytem has be  sensitive and capable enough to detect and classify both emotions and intent so that  it does not present wrong offering or messages to the customer at teh wrong point of time .

7. The system has to be capable of  extracting missing or unstructured  infromation and convert it into proper validated json format. That can be used as response for the webapp endpoints.

8. The System has to work in both chat and button pressing mode which is facilitated by whatsapp apis. Part of the work flow can be in the chat and another part in button press. Both condition should facilitate  prevention of race condition during state transtions from name_collection to booking ...etc

9. The system has to recover from state locks (like getting stuck in address_collection ,name_collection or car_details_collection or forgetting already connected infromation  and ending up asking the information again  and annoying the customer. )

10. The System uses llms for classification and response genration and data organisation. It has been observed during the  creation of previous prototypes of this chatbot,the system fails catastrophically  and silently in a way where the root of the error cannot be  mapped out to single subsystem  down to  bunch of lines of a  specfic  module,there can also be network failures ,timeouts resulting in a very poor customer expierence .
We would like to prevent in this case.

## Resources

1. [Details Regarding whatsapp Integration is given in](wapi_endpioints.md)
2. [Details Regarding Webapp Endpoints is given in](frappe_api.md)
