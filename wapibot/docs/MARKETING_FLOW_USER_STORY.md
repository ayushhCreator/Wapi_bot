# User Story: Lead-to-Registration Marketing Flow

## Overview

A comprehensive conversational flow from initial marketing outreach to either website registration (new users) or service booking (existing users), using WapiBot as the engagement layer for Yawlit Automotives.

---

## User Journey Map

```bash
Marketing Message (WhatsApp Blast)
        ↓
Customer Receives Message → Reads → Replies "YES"
        ↓
Bot Checks Customer Status (via phone number from WhatsApp)
        ↓           ↓
    NEW USER    EXISTING USER
        ↓           ↓
   Path A       Path B
```

---

## Path A: New User Journey (Lead-to-Registration)

### Step 1: Initial Marketing Message (Outbound)

**Trigger:** Manual WhatsApp blast to lead database

**Message Content (Template):**

```bash
🚗 Yawlit Automotives – Smarter Car Care Starts Here

We're India's 1st to introduce the Dark Store Model in car servicing:
🔹 Centralised spare procurement = Lower cost, faster service
🔹 OEM-level quality, full transparency, end-to-end control
🔹 Covers all cars, with dedicated setups for premium brands

💼 Services we offer:
✅ Maintenance & Repairs
✅ Insurance Buy/Renew + Claims
✅ Body Work (Insurance Covered)
✅ OEM/Aftermarket/Refurbished Spares
✅ Accessories for Functionality & Style

💎 Premium car? We've got separate dark garages & expert tools.
🛠️ AC, mechanical, electrical — all heavy-duty work handled.
🚚 Free Doorstep Pickup & Drop
💰 Save 40–50% vs service centers
📊 1000+ cars serviced | ₹40+ Lakhs saved

💬 Reply "YES" to experience the future of car servicing.
```

**Technical Implementation:**

- Create atomic node: `nodes/marketing/send_template_message.py`
- Store template in: `config/message_templates.yaml`
- Track delivery status in conversation state

---

### Step 2: Customer Engagement ("YES" Response)

**User Action:** Replies with "YES" (or variations: "yes", "Yes", "sure", "okay", "interested")

**Bot Recognition Logic:**

- Extract intent from message
- Classify as: `intent="interested_in_service"`
- Match against engagement triggers: ["yes", "sure", "okay", "interested", "tell me more"]

**Bot Response:**

```bash
Great! I'm excited to help you.

To get started, I need a few quick details:
1️⃣ What's your name?
```

**State Update:**

```python
state["intent"] = "interested_in_service"
state["engagement_status"] = "engaged"
state["current_step"] = "collect_name"
state["is_new_user"] = True
```

---

### Step 3: Information Collection Phase

#### 3a. Collect Name

**User Input:** "My name is Rahul Kumar"

**Bot Processing:**

1. Extract name using DSPy `NameExtractor`
2. Validate using Pydantic `Name` model
3. Store with confidence score

**State Update:**

```python
state["customer"] = {
    "first_name": "Rahul",
    "last_name": "Kumar",
    "full_name": "Rahul Kumar",
    "extraction_metadata": {
        "confidence": 0.95,
        "source": "dspy_extractor",
        "timestamp": "2025-01-15T10:30:00"
    }
}
```

**Bot Response:**

```bash
Thanks Rahul!

2️⃣ What's your phone number?
```

---

#### 3b. Collect Phone Number

**User Input:** "9876543210" or "+91 9876543210"

**Bot Processing:**

1. Extract phone using DSPy `PhoneExtractor`
2. Normalize format (remove +91, spaces, dashes)
3. Validate Indian phone number format (10 digits, starts with 6-9)
4. **CRITICAL CHECK:** Call Yawlit API to verify if customer exists

**API Call:**

```python
# File: clients/frappe_yawlit/customer/lookup_client.py
result = await client.customer_lookup.check_customer_exists("9876543210")

# Returns:
# {"exists": False} for new users
# {"exists": True, "data": {...}} for existing users
```

**Branching Logic:**

- If `exists=True` → **Redirect to Path B (Existing User)**
- If `exists=False` → Continue Path A (New User)

**Assumption for Path A:** Phone number not found in Yawlit database

**State Update:**

```python
state["customer"]["phone_number"] = "9876543210"
state["customer_exists"] = False
state["current_step"] = "collect_vehicle"
```

**Bot Response:**

```bash
Perfect!

3️⃣ Tell me about your car:
   - Which brand and model?
   - What's the registration number?

Example: "Honda City, KA01AB1234"
```

---

#### 3c. Collect Vehicle Information

**User Input (Combined):** "Honda City, KA01AB1234"
**OR**
**User Input (Sequential):**

- "Honda City"
- *(next message)* "KA01AB1234"

**Bot Processing:**

1. Extract vehicle using DSPy `VehicleExtractor`
2. Parse brand, model, registration number
3. Validate license plate format (Indian standards)
4. Determine vehicle type (Sedan/SUV/Hatchback) via lookup table

**Vehicle Type Mapping (Implicit Logic):**

```python
VEHICLE_TYPE_MAPPING = {
    "Honda City": "Sedan",
    "Honda Civic": "Sedan",
    "Maruti Swift": "Hatchback",
    "Maruti Brezza": "SUV",
    "Toyota Fortuner": "SUV",
    "Hyundai Creta": "SUV",
    "Tata Nexon": "SUV",
    # ... comprehensive mapping
}
```

**State Update:**

```python
state["vehicle"] = {
    "brand": "Honda",
    "model": "City",
    "number_plate": "KA01AB1234",
    "vehicle_type": "Sedan",  # Derived from mapping
    "extraction_metadata": {
        "confidence": 0.90,
        "source": "dspy_extractor"
    }
}
```

**Bot Response:**

```bash
Awesome! Honda City (Sedan) — great choice!

4️⃣ What kind of service are you looking for?
   - Regular maintenance
   - Repairs
   - Insurance
   - AC service
   - Or just exploring options?
```

---

#### 3d. Collect Service Interest (Optional for Registration)

**User Input:** "Regular maintenance" or "Just exploring"

**Bot Processing:**

1. Classify service intent
2. Store for future reference (not required for registration)

**State Update:**

```python
state["service_interest"] = "regular_maintenance"
state["current_step"] = "ready_for_registration"
```

**Bot Response:**

```bash
Got it!

Before we proceed with booking, I need you to complete a quick registration on our website. This will give you access to:

✅ Real-time service tracking
✅ Digital service history
✅ Instant quotes
✅ Exclusive member discounts
✅ Priority booking

👉 Register here: https://yawlit.duckdns.org/register

Once you're registered, come back and I'll help you book your service right away!

*Your details so far:*
Name: Rahul Kumar
Phone: 9876543210
Vehicle: Honda City (KA01AB1234)
```

---

### Step 4: Send Registration Link

**Technical Implementation:**

**Node:** `nodes/onboarding/send_registration_link.py`

```python
async def send_registration_link(state: BookingState) -> BookingState:
    """Send registration link with pre-filled data."""

    customer = state.get("customer", {})
    vehicle = state.get("vehicle", {})

    # Build pre-filled URL (optional, for better UX)
    base_url = "https://yawlit.duckdns.org/register"
    params = {
        "name": customer.get("full_name", ""),
        "phone": customer.get("phone_number", ""),
        "vehicle_brand": vehicle.get("brand", ""),
        "vehicle_model": vehicle.get("model", ""),
        "vehicle_number": vehicle.get("number_plate", ""),
    }

    # URL encode parameters
    registration_url = f"{base_url}?{urlencode(params)}"

    # Construct message
    message = format_registration_message(customer, vehicle, registration_url)

    state["response"] = message
    state["registration_link_sent"] = True
    state["awaiting_registration"] = True
    state["current_step"] = "awaiting_website_registration"

    return state
```

**WAPI Integration (Future Enhancement):**

```python
# Send as button/link message (WAPI feature)
await wapi_client.send_button_message(
    phone_number=state["conversation_id"],
    text="Complete your registration to continue:",
    buttons=[
        {"type": "url", "text": "Register Now", "url": registration_url}
    ]
)
```

---

### Step 5: Post-Registration Follow-up

**Trigger:** User returns after registration OR asks follow-up question

**User Message:** "I registered" or "Done" or "What's next?"

**Bot Response:**

```bash
Awesome! Welcome to Yawlit, Rahul! 🎉

Your profile is now active.

Now, let's book your first service:
- What date works for you?
- Morning (9 AM - 12 PM) or afternoon (2 PM - 5 PM)?

We'll handle pickup and drop-off from your location!
```

**Verification (Optional):**

- Re-check customer existence via API
- If found: Load full profile
- If not found: Politely ask to complete registration

---

## Path B: Existing User Journey (Service Booking)

### Step 1: Customer Status Check (Immediate)

**Trigger:** User replies to marketing message with "YES"

**Bot Processing:**

1. Extract phone number from WhatsApp metadata (`payload.contact.phone_number`)
2. Call Yawlit customer lookup API
3. Load customer profile

**API Calls:**

```python
# Check customer existence
exists_result = await client.customer_lookup.check_customer_exists(phone)

if exists_result["exists"]:
    # Load full profile
    profile = await client.customer_profile.get_profile()

    # Load vehicles
    vehicles = await client.customer_profile.get_vehicles()

    # Load recent bookings (optional)
    bookings = await client.customer_lookup.get_customer_bookings(limit=5)

    # Load active subscriptions (optional)
    subscriptions = await client.customer_lookup.get_customer_subscriptions()
```

**State Update:**

```python
state["customer_exists"] = True
state["customer"] = {
    "uuid": "CUST-2025-001",
    "first_name": "Amit",
    "last_name": "Sharma",
    "phone_number": "9123456789",
    "email": "amit@example.com"
}
state["vehicles"] = [
    {
        "vehicle_number": "DL01AB1234",
        "vehicle_make": "Honda",
        "vehicle_model": "City",
        "vehicle_type": "Sedan"
    },
    {
        "vehicle_number": "DL02CD5678",
        "vehicle_make": "Toyota",
        "vehicle_model": "Fortuner",
        "vehicle_type": "SUV"
    }
]
state["is_new_user"] = False
```

---

### Step 2: Personalized Greeting

**Bot Response:**

```bash
Welcome back, Amit! 👋

Great to hear from you! I see you have:
🚗 Honda City (DL01AB1234)
🚙 Toyota Fortuner (DL02CD5678)

Which car needs servicing today?
```

**State Update:**

```python
state["current_step"] = "select_vehicle"
state["awaiting_vehicle_selection"] = True
```

---

### Step 3: Vehicle Selection (Multi-Car Scenario)

**User Input:** "Honda City" or "The sedan" or "First one"

**Bot Processing:**

1. Match user input against owned vehicles
2. Disambiguate if unclear
3. Set active vehicle for booking

**State Update:**

```python
state["selected_vehicle"] = {
    "vehicle_number": "DL01AB1234",
    "vehicle_make": "Honda",
    "vehicle_model": "City",
    "vehicle_type": "Sedan"
}
state["current_step"] = "show_services"
```

**Bot Response:**

```bash
Perfect! Honda City it is.

Here are services available for Sedan:

🔧 Regular Maintenance
   - Oil Change + Filter - ₹1,200
   - General Service (20+ checks) - ₹2,500
   - Major Service (50+ checks) - ₹5,000

🚿 Cleaning & Detailing
   - Basic Wash - ₹300
   - Premium Wash + Interior - ₹800
   - Full Detail + Coating - ₹5,500

🛠️ Repairs
   - AC Service - ₹1,500
   - Brake Service - ₹2,000
   - Suspension Check - ₹1,800

💎 Subscription Plans (Save 40%)
   - Basic Plan - ₹3,000/month
   - Premium Plan - ₹5,000/month

What are you interested in?
```

---

### Step 4: Service Filtering Logic (Implicit)

**Vehicle Type Filtering:**

```python
# File: nodes/services/filter_services_by_vehicle.py

async def filter_services_by_vehicle(state: BookingState) -> BookingState:
    """Filter services based on selected vehicle type."""

    vehicle = state.get("selected_vehicle", {})
    vehicle_type = vehicle.get("vehicle_type")  # "Sedan", "SUV", "Hatchback"

    # Call Yawlit API with filter
    services = await client.catalog.get_filtered_services(
        vehicle_type=vehicle_type,
        category=None,  # Show all categories initially
        frequency_type=None
    )

    # Group by category for presentation
    categorized_services = group_services_by_category(services)

    state["available_services"] = services
    state["categorized_services"] = categorized_services

    return state
```

**Service Presentation Format:**

```python
def format_service_list(categorized_services: dict) -> str:
    """Format services into readable WhatsApp message."""

    message_parts = []

    for category, services in categorized_services.items():
        message_parts.append(f"\n{category_emoji(category)} {category}")

        for service in services[:3]:  # Limit to top 3 per category
            message_parts.append(
                f"   - {service['name']} - ₹{service['price']}"
            )

        if len(services) > 3:
            message_parts.append(f"   ... and {len(services) - 3} more")

    return "\n".join(message_parts)
```

---

### Step 5: Service Selection & Booking

**User Input:** "General Service"

**Bot Processing:**

1. Match service name
2. Fetch service details and addons
3. Show pricing and available slots

**API Call:**

```python
service_details = await client.catalog.get_service_details(service_id)
addons = await client.catalog.get_optional_addons(service_id)
```

**Bot Response:**

```bash
Great choice! General Service for Honda City

📋 Included:
   - Engine oil change
   - Oil filter replacement
   - 20+ point inspection
   - Brake check
   - Tire rotation

💰 Price: ₹2,500 (Save 45% vs service center)
⏱️ Duration: 2-3 hours
🚚 Free pickup & drop included

Optional Add-ons:
   + AC Filter Cleaning - ₹300
   + Interior Vacuum - ₹200

When would you like to schedule this?
```

---

### Step 6: Appointment Scheduling

**User Input:** "Tomorrow morning"

**Bot Processing:**

1. Parse date and time preference
2. Fetch available slots from Yawlit API
3. Show slot options

**API Call:**

```python
slots = await client.booking.get_available_slots(
    service_id="SRV-2025-100",
    date="2025-01-16",
    time_preference="morning",
    location=customer_location
)
```

**Bot Response:**

```bash
Available slots for tomorrow (Jan 16):

🌅 Morning:
   1. 9:00 AM - 12:00 PM
   2. 10:00 AM - 1:00 PM

Which slot works for you?
```

---

### Step 7: Booking Confirmation

**User Input:** "9 AM slot"

**Bot Processing:**

1. Create booking via Yawlit API
2. Generate booking confirmation
3. Send confirmation message

**API Call:**

```python
booking = await client.booking.create_booking({
    "customer_uuid": state["customer"]["uuid"],
    "service_id": "SRV-2025-100",
    "vehicle_id": state["selected_vehicle"]["vehicle_number"],
    "slot_id": "SLOT-2025-150",
    "date": "2025-01-16",
    "pickup_address": customer_address,
    "addons": [],
    "total_amount": 2500
})
```

**Bot Response:**

```bash
✅ Booking Confirmed!

📅 Service: General Service
🚗 Vehicle: Honda City (DL01AB1234)
📍 Pickup: Your registered address
🕒 Date & Time: Jan 16, 9:00 AM - 12:00 PM
💰 Amount: ₹2,500

Booking ID: BKG-2025-500

We'll send a pickup driver 30 mins before your slot. You'll receive live updates via WhatsApp.

Need anything else?
```

**State Update:**

```python
state["booking_completed"] = True
state["service_request_id"] = "BKG-2025-500"
state["service_request"] = booking_details
state["current_step"] = "booking_complete"
```

---

## Implicit Requirements Made Explicit

### 1. Customer Lookup Mechanism

**When:** Immediately upon receiving user's first message (after marketing blast)

**How:**

1. Extract phone number from WAPI webhook payload
2. Normalize phone number format
3. Call `/api/method/frappe.client.get_value` at Yawlit backend
4. Cache result in conversation state

**API Endpoint:**

```bash
POST https://yawlit.duckdns.org/api/method/frappe.client.get_value
Body: {
    "doctype": "User",
    "filters": {"phone": "9876543210"},
    "fieldname": ["name", "customer_uuid", "enabled"]
}
```

**Decision Tree:**

```python
if customer_exists:
    if customer_has_vehicles:
        if len(vehicles) > 1:
            ask_which_vehicle()
        else:
            auto_select_vehicle()
        show_services_for_vehicle_type()
    else:
        ask_to_add_vehicle_first()
else:
    start_new_user_onboarding()
```

---

### 2. Vehicle Type Determination

**Implicit Logic:** Vehicle type (Sedan/SUV/Hatchback) must be determined to filter services

**Implementation Options:**

#### **Option A: Lookup Table (Recommended for MVP Stage)**

```python
# File: config/vehicle_type_mapping.py
VEHICLE_TYPE_MAP = {
    "Honda City": "Sedan",
    "Honda Civic": "Sedan",
    "Honda Amaze": "Sedan",
    "Maruti Swift": "Hatchback",
    "Maruti Dzire": "Sedan",
    "Maruti Brezza": "SUV",
    # ... 500+ entries
}

def get_vehicle_type(brand: str, model: str) -> str:
    key = f"{brand} {model}"
    return VEHICLE_TYPE_MAP.get(key, "Unknown")
```

#### **Option B: Yawlit API Call**

```python
vehicle_info = await client.catalog.get_vehicle_types()
# Assumes Yawlit has vehicle master data
```

#### **Option C: DSPy Classification (ML-based)**

```python
# Train DSPy classifier on vehicle descriptions
vehicle_type = VehicleTypeClassifier().forward(f"{brand} {model}")
```

---

### 3. Service Catalog Presentation

**Implicit Requirements:**

- Services must be filtered by vehicle type
- Show pricing in Indian Rupees (₹)
- Group by category for readability
- Limit initial display (avoid message overflow)
- Support drill-down (category → services → details → addons)

**Message Size Constraint:**

- WhatsApp has ~4096 character limit per message
- Solution: Paginate or use category-based navigation

**Navigation Pattern:**

```bash
Show Categories → User picks category → Show services in that category →
User picks service → Show details + addons → User confirms → Schedule appointment
```

---

### 4. Registration Data Flow

**Implicit Requirement:** Data collected in chat should pre-fill registration form

**Technical Implementation:**

**SECURITY REQUIREMENT:** Personal details (name, phone, vehicle info) MUST NOT be passed in URL query parameters. This would expose sensitive data in browser history, server logs, referrer headers, and network traffic.

**Secure Token-Based Approach:**

```python
# Create temporary lead record in Yawlit backend
lead = await client.leads.create_lead({
    "source": "whatsapp_bot",
    "name": "Rahul Kumar",
    "phone": "9876543210",
    "vehicle_brand": "Honda",
    "vehicle_model": "City",
    "vehicle_number": "KA01AB1234",
    "status": "registration_pending"
})

# Generate unique, time-limited token (expires in 24 hours)
registration_token = generate_secure_token(
    lead_id=lead.id,
    expiry_hours=24
)

# Send link with ONLY the token
url = f"https://yawlit.duckdns.org/register?token={registration_token}"
```

**Form Auto-Fill on Website:**

```javascript
// On registration page
const urlParams = new URLSearchParams(window.location.search);
const token = urlParams.get('token');

if (token) {
    fetch(`/api/method/get_lead_data?token=${token}`)
        .then(data => {
            document.getElementById('name').value = data.name;
            document.getElementById('phone').value = data.phone;
            // ... pre-fill form
        });
}
```

---

### 5. Multi-Car Owner Service Filtering

**Implicit Logic:** When user owns multiple cars of different types (e.g., Sedan + SUV), only show services applicable to the selected vehicle

**Example Scenario:**

- User owns: Honda City (Sedan) + Toyota Fortuner (SUV)
- User selects: Honda City
- Bot filters services: `vehicle_type = "Sedan"`
- Result: SUV-specific services (e.g., "Heavy Duty Suspension") are hidden

**API Call:**

```python
services = await client.catalog.get_filtered_services(
    vehicle_type="Sedan",  # From selected vehicle
    category=None,
    frequency_type=None
)
```

---

### 6. Engagement & Re-engagement

**Implicit Requirements:**

**Low Engagement Scenario:**

- User reads marketing message but doesn't reply
- Action: Send follow-up after 24-48 hours

**Partial Engagement Scenario:**

- User replies "YES" but doesn't complete registration
- Action: Send reminder after 2 hours

**Drop-off Detection:**

- User starts info collection but stops mid-conversation
- Action: Send re-engagement message with saved progress

**Example Follow-up:**

```bash
Hi Rahul,

I noticed you were interested in our services yesterday.

Your details are saved:
- Name: Rahul Kumar
- Vehicle: Honda City

Ready to complete registration? Just reply and we'll pick up where we left off!
```

---

### 7. Smart Conversation Handling

**Implicit Requirements:**

**Typo Tolerance:**

- "yse" → "yes"
- "hoda city" → "Honda City"
- "confrim" → "confirm"

**Intent Variations:**

- "yes" / "sure" / "interested" / "ok" → `intent="interested"`
- "nah" / "no thanks" / "not interested" → `intent="declined"`

**Clarification Handling:**

- User: "What services do you offer?"
- Bot: *(Re-send service categories without asking for vehicle)*

**Context Retention:**

- User provides name, then asks "what was I supposed to tell you?"
- Bot: "Next, I need your phone number"

---

## LangGraph Workflow Architecture

### Workflow File: `workflows/marketing_to_registration_workflow.py`

```python
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.marketing import send_template_message
from nodes.onboarding import (
    check_customer_status,
    collect_basic_info,
    send_registration_link
)
from nodes.services import (
    select_vehicle,
    filter_services_by_vehicle,
    present_service_catalog,
    show_service_details
)
from nodes.booking import (
    schedule_appointment,
    create_booking,
    send_confirmation
)

def create_marketing_workflow() -> StateGraph:
    """Marketing-to-registration complete workflow."""

    workflow = StateGraph(BookingState)

    # === Phase 1: Initial Engagement ===
    workflow.add_node("send_marketing_message", send_template_message)
    workflow.add_node("check_customer", check_customer_status)

    # === Phase 2A: New User Path ===
    workflow.add_node("collect_name", collect_basic_info("name"))
    workflow.add_node("collect_phone", collect_basic_info("phone"))
    workflow.add_node("collect_vehicle", collect_basic_info("vehicle"))
    workflow.add_node("collect_service_interest", collect_basic_info("service"))
    workflow.add_node("send_registration", send_registration_link)

    # === Phase 2B: Existing User Path ===
    workflow.add_node("load_customer_profile", load_profile_from_yawlit)
    workflow.add_node("greet_existing_customer", greet_returning_user)
    workflow.add_node("ask_which_vehicle", select_vehicle)
    workflow.add_node("filter_services", filter_services_by_vehicle)
    workflow.add_node("show_services", present_service_catalog)
    workflow.add_node("show_details", show_service_details)
    workflow.add_node("schedule_slot", schedule_appointment)
    workflow.add_node("confirm_booking", create_booking)
    workflow.add_node("send_booking_confirmation", send_confirmation)

    # === Entry Point ===
    workflow.set_entry_point("check_customer")

    # === Routing: New vs Existing ===
    workflow.add_conditional_edges(
        "check_customer",
        lambda s: "existing" if s.get("customer_exists") else "new",
        {
            "new": "collect_name",
            "existing": "load_customer_profile"
        }
    )

    # === New User Flow ===
    workflow.add_edge("collect_name", "collect_phone")
    workflow.add_edge("collect_phone", "collect_vehicle")
    workflow.add_edge("collect_vehicle", "collect_service_interest")
    workflow.add_edge("collect_service_interest", "send_registration")
    workflow.add_edge("send_registration", END)

    # === Existing User Flow ===
    workflow.add_edge("load_customer_profile", "greet_existing_customer")
    workflow.add_conditional_edges(
        "greet_existing_customer",
        lambda s: "multi" if len(s.get("vehicles", [])) > 1 else "single",
        {
            "multi": "ask_which_vehicle",
            "single": "filter_services"  # Auto-select single vehicle
        }
    )
    workflow.add_edge("ask_which_vehicle", "filter_services")
    workflow.add_edge("filter_services", "show_services")
    workflow.add_edge("show_services", "show_details")
    workflow.add_edge("show_details", "schedule_slot")
    workflow.add_edge("schedule_slot", "confirm_booking")
    workflow.add_edge("confirm_booking", "send_booking_confirmation")
    workflow.add_edge("send_booking_confirmation", END)

    return workflow

# Compile
marketing_workflow = create_marketing_workflow().compile()
```

---

## Required Nodes to Implement

### Marketing Nodes

1. **`nodes/marketing/send_template_message.py`**
   - Purpose: Send initial marketing message
   - Input: Template ID or text
   - Output: Message sent confirmation

---

### Onboarding Nodes (New Users)

1. **`nodes/onboarding/check_customer_status.py`**
   - Purpose: Call Yawlit API to check if customer exists
   - API: `POST /api/method/frappe.client.get_value`
   - Logic: Extract phone → normalize → API call → set `customer_exists` flag

2. **`nodes/onboarding/collect_basic_info.py`** (Generic collector)
   - Purpose: Extract name/phone/vehicle/service interest
   - Uses: Existing atomic `extract_node`
   - Variants: `collect_basic_info("name")`, `collect_basic_info("phone")`, etc.

3. **`nodes/onboarding/send_registration_link.py`**
   - Purpose: Generate and send registration URL
   - Logic: Pre-fill URL parameters OR create lead token
   - Output: WhatsApp message with clickable link

---

### Customer Management Nodes (Existing Users)

1. **`nodes/customer/load_profile_from_yawlit.py`**
   - Purpose: Fetch full customer profile, vehicles, bookings
   - APIs:
     - `get_customer_profile()`
     - `get_customer_vehicles()`
     - `get_customer_bookings(limit=5)`

2. **`nodes/customer/greet_returning_user.py`**
   - Purpose: Personalized greeting with vehicle list
   - Template: "Welcome back, {name}! I see you have: {vehicles}"

---

### Service Presentation Nodes

1. **`nodes/services/select_vehicle.py`**
   - Purpose: Ask user which car (for multi-car owners)
   - Logic: Present vehicle list → capture selection → validate

2. **`nodes/services/filter_services_by_vehicle.py`**
   - Purpose: Filter services by vehicle type
   - API: `get_filtered_services(vehicle_type="Sedan")`
   - Logic: Extract vehicle type → call API → store filtered list

3. **`nodes/services/present_service_catalog.py`**
   - Purpose: Format and display categorized services
   - Logic: Group by category → limit display → add emojis → send message

4. **`nodes/services/show_service_details.py`**
    - Purpose: Show pricing, inclusions, addons for selected service
    - API: `get_service_details(service_id)`, `get_optional_addons(service_id)`

---

### Booking Nodes

1. **`nodes/booking/schedule_appointment.py`**
    - Purpose: Parse date/time preference → fetch slots → present options
    - API: `get_available_slots(service_id, date, time_preference)`

2. **`nodes/booking/create_booking.py`**
    - Purpose: Create booking in Yawlit system
    - API: `create_booking({customer_uuid, service_id, vehicle_id, slot_id, ...})`

3. **`nodes/booking/send_confirmation.py`**
    - Purpose: Send booking confirmation message with details
    - Template: Booking ID, service, vehicle, date/time, amount

---

## Configuration Files

### Message Templates

**File:** `config/message_templates.yaml`

```yaml
marketing_blast:
  text: |
    🚗 Yawlit Automotives – Smarter Car Care Starts Here

    We're India's 1st to introduce the Dark Store Model in car servicing:
    🔹 Centralised spare procurement = Lower cost, faster service
    🔹 OEM-level quality, full transparency, end-to-end control
    🔹 Covers all cars, with dedicated setups for premium brands

    💼 Services we offer:
    ✅ Maintenance & Repairs
    ✅ Insurance Buy/Renew + Claims
    ✅ Body Work (Insurance Covered)
    ✅ OEM/Aftermarket/Refurbished Spares
    ✅ Accessories for Functionality & Style

    💎 Premium car? We've got separate dark garages & expert tools.
    🛠️ AC, mechanical, electrical — all heavy-duty work handled.
    🚚 Free Doorstep Pickup & Drop
    💰 Save 40–50% vs service centers
    📊 1000+ cars serviced | ₹40+ Lakhs saved

    💬 Reply "YES" to experience the future of car servicing.

registration_prompt:
  text: |
    Before we proceed with booking, I need you to complete a quick registration on our website. This will give you access to:

    ✅ Real-time service tracking
    ✅ Digital service history
    ✅ Instant quotes
    ✅ Exclusive member discounts
    ✅ Priority booking

    👉 Register here: {registration_url}

    Once you're registered, come back and I'll help you book your service right away!

    *Your details so far:*
    Name: {customer_name}
    Phone: {customer_phone}
    Vehicle: {vehicle_brand} {vehicle_model} ({vehicle_number})

existing_user_greeting:
  text: |
    Welcome back, {customer_name}! 👋

    Great to hear from you! I see you have:
    {vehicle_list}

    Which car needs servicing today?

booking_confirmation:
  text: |
    ✅ Booking Confirmed!

    📅 Service: {service_name}
    🚗 Vehicle: {vehicle_brand} {vehicle_model} ({vehicle_number})
    📍 Pickup: {pickup_address}
    🕒 Date & Time: {appointment_date}, {appointment_time}
    💰 Amount: ₹{total_amount}

    Booking ID: {booking_id}

    We'll send a pickup driver 30 mins before your slot. You'll receive live updates via WhatsApp.

    Need anything else?
```

---

### Vehicle Type Mapping

**File:** `config/vehicle_type_mapping.py`

```python
VEHICLE_TYPE_MAP = {
    # Honda
    "Honda City": "Sedan",
    "Honda Civic": "Sedan",
    "Honda Accord": "Sedan",
    "Honda Amaze": "Sedan",
    "Honda Jazz": "Hatchback",
    "Honda WR-V": "SUV",
    "Honda CR-V": "SUV",

    # Maruti Suzuki
    "Maruti Swift": "Hatchback",
    "Maruti Dzire": "Sedan",
    "Maruti Baleno": "Hatchback",
    "Maruti Brezza": "SUV",
    "Maruti Ertiga": "SUV",
    "Maruti S-Cross": "SUV",

    # Hyundai
    "Hyundai i20": "Hatchback",
    "Hyundai Verna": "Sedan",
    "Hyundai Creta": "SUV",
    "Hyundai Venue": "SUV",
    "Hyundai Tucson": "SUV",

    # Toyota
    "Toyota Fortuner": "SUV",
    "Toyota Innova": "SUV",
    "Toyota Camry": "Sedan",
    "Toyota Glanza": "Hatchback",

    # Tata
    "Tata Nexon": "SUV",
    "Tata Harrier": "SUV",
    "Tata Safari": "SUV",
    "Tata Altroz": "Hatchback",
    "Tata Tigor": "Sedan",

    # Add 400+ more mappings
}

def get_vehicle_type(brand: str, model: str) -> str:
    """Determine vehicle type from brand and model."""
    key = f"{brand} {model}"
    return VEHICLE_TYPE_MAP.get(key, "Unknown")
```

---

## Database / State Tracking

### Conversation State Schema (Extended)

```python
class BookingState(TypedDict):
    # === Existing Fields ===
    conversation_id: str
    user_message: str
    history: List[Dict[str, str]]

    # === Customer Data ===
    customer_exists: bool  # NEW
    is_new_user: bool  # NEW
    customer: Optional[Dict[str, Any]]
    vehicles: Optional[List[Dict[str, Any]]]  # NEW: For multi-car owners
    selected_vehicle: Optional[Dict[str, Any]]  # NEW: Currently selected car

    # === Service Discovery ===
    available_services: Optional[List[Dict[str, Any]]]  # NEW
    categorized_services: Optional[Dict[str, List]]  # NEW
    selected_service: Optional[Dict[str, Any]]  # NEW
    service_interest: Optional[str]  # NEW: For new users

    # === Registration Flow ===
    registration_link_sent: bool  # NEW
    awaiting_registration: bool  # NEW
    registration_completed: bool  # NEW

    # === Booking Data ===
    appointment: Optional[Dict[str, Any]]
    service_request_id: Optional[str]
    service_request: Optional[Dict[str, Any]]

    # === Workflow Control ===
    current_step: str
    engagement_status: str  # NEW: "engaged", "partial", "dropped"
    completeness: float

    # === Response ===
    response: str
    should_confirm: bool
```

---

## API Integration Summary

### Yawlit Backend Base URL

```bash
https://yawlit.duckdns.org
```

### Required API Endpoints

| Purpose | Endpoint | Method |
|---------|----------|--------|

| Check customer exists | `/api/method/frappe.client.get_value` | POST |
| Get customer profile | `/api/method/yawlit_automotive_services.api.customer_portal.get_customer_profile` | POST |
| Get customer vehicles | `/api/method/yawlit_automotive_services.api.customer_portal.get_customer_vehicles` | POST |
| Get filtered services | `/api/method/yawlit_automotive_services.api.catalog.get_filtered_services` | POST |
| Get service details | `/api/method/yawlit_automotive_services.api.catalog.get_service_details` | POST |
| Get optional addons | `/api/method/yawlit_automotive_services.api.catalog.get_optional_addons` | POST |
| Get available slots | `/api/method/yawlit_automotive_services.api.booking.get_available_slots` | POST |
| Create booking | `/api/method/yawlit_automotive_services.api.booking.create_booking` | POST |
| Create lead (optional) | `/api/method/yawlit_automotive_services.api.leads.create_lead` | POST |

### Authentication

```python
headers = {
    "Authorization": f"token {api_key}:{api_secret}",
    "Content-Type": "application/json"
}
```

---

## Testing Strategy

### Test Scenario 1: New User (Happy Path)

```bash
1. Send marketing message
2. User replies "YES"
3. Bot checks: customer_exists = False
4. Bot asks for name → User provides
5. Bot asks for phone → User provides
6. Bot asks for vehicle → User provides
7. Bot sends registration link
8. ✅ Expected: Registration URL with pre-filled data
```

### Test Scenario 2: Existing User - Single Car

```bash
1. Send marketing message
2. User replies "YES"
3. Bot checks: customer_exists = True, vehicles = [Honda City]
4. Bot greets: "Welcome back! I see you have Honda City"
5. Bot auto-selects vehicle, shows services filtered for Sedan
6. User picks service → Bot shows details
7. User schedules → Bot creates booking
8. ✅ Expected: Booking confirmation with BKG-ID
```

### Test Scenario 3: Existing User - Multiple Cars

```bash
1. Send marketing message
2. User replies "YES"
3. Bot checks: customer_exists = True, vehicles = [Honda City, Toyota Fortuner]
4. Bot asks: "Which car? Honda City or Toyota Fortuner?"
5. User: "Honda City"
6. Bot filters services for Sedan only
7. User picks service → proceeds to booking
8. ✅ Expected: Only Sedan services shown, not SUV services
```

### Test Scenario 4: User Drop-off & Re-engagement

```bash
1. User starts flow, provides name
2. User doesn't respond after phone request
3. Wait 2 hours
4. Bot sends: "Hi {name}, ready to continue? I still need your phone number"
5. User resumes → completes registration
6. ✅ Expected: Conversation state preserved, seamless continuation
```

---

## Success Metrics

### New User Conversion

- **Metric:** % of users who click registration link after providing info
- **Target:** >60%

### Existing User Booking Rate

- **Metric:** % of existing users who complete booking within conversation
- **Target:** >40%

### Response Time

- **Metric:** Avg time from user message to bot response
- **Target:** <3 seconds

### Drop-off Rate

- **Metric:** % of users who stop mid-conversation
- **Target:** <30%

### Re-engagement Success

- **Metric:** % of dropped users who resume after follow-up
- **Target:** >20%

---

## Critical Files to Modify/Create

### New Files (13 nodes + 2 configs)

1. `backend/src/nodes/marketing/send_template_message.py`
2. `backend/src/nodes/onboarding/check_customer_status.py`
3. `backend/src/nodes/onboarding/collect_basic_info.py`
4. `backend/src/nodes/onboarding/send_registration_link.py`
5. `backend/src/nodes/customer/load_profile_from_yawlit.py`
6. `backend/src/nodes/customer/greet_returning_user.py`
7. `backend/src/nodes/services/select_vehicle.py`
8. `backend/src/nodes/services/filter_services_by_vehicle.py`
9. `backend/src/nodes/services/present_service_catalog.py`
10. `backend/src/nodes/services/show_service_details.py`
11. `backend/src/nodes/booking/schedule_appointment.py`
12. `backend/src/nodes/booking/create_booking.py`
13. `backend/src/nodes/booking/send_confirmation.py`
14. `backend/src/config/message_templates.yaml`
15. `backend/src/config/vehicle_type_mapping.py`

### New Workflow

1. `backend/src/workflows/marketing_to_registration_workflow.py`

### Modified Files

1. `backend/src/workflows/shared/state.py` - Add new state fields
2. `backend/src/api/v1/wapi_webhook.py` - Route to new workflow

### Documentation

1. `docs/MARKETING_FLOW_USER_STORY.md` - This document

---

## Future Enhancements (Out of Scope for Now)

1. **Full Chat-Based Registration** - Complete registration without website
2. **Payment Integration** - Handle payments within WhatsApp
3. **Service Recommendations** - ML-based service suggestions
4. **Loyalty Program** - Points tracking and rewards
5. **Multi-Language Support** - Hindi, Tamil, Telugu, etc.
6. **Voice Input** - Accept voice messages for vehicle details
7. **Image Processing** - Upload vehicle photos for condition assessment
8. **Subscription Management** - Upgrade/downgrade plans in chat
9. **Referral System** - "Refer a friend" feature
10. **Feedback Collection** - Post-service rating and reviews

---

## Summary

This user story comprehensively covers:

✅ **Path A:** New user journey from marketing message to registration
✅ **Path B:** Existing user journey from greeting to booking confirmation
✅ **Implicit requirements** made explicit (customer lookup, vehicle filtering, service presentation)
✅ **LangGraph workflow architecture** with conditional routing
✅ **13 new nodes** required for implementation
✅ **API integration** with Yawlit backend
✅ **State management** extensions
✅ **Testing scenarios** for validation
✅ **Configuration files** for templates and vehicle mapping

This forms a complete blueprint for implementing the marketing-to-registration conversational flow in the WapiBot backend.
