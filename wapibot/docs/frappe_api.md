# Booking Flow API Analysis & Documentation

**Date:** 2025-12-22
**Module:** `yawlit_automotive_services`

This document details the backend Python APIs used in the one-time booking flow (`www/customer/book-service`). It maps frontend `frappe.call` methods to their backend implementations, explaining parameters, return values, and critical business logic.

---

## 1. Service Discovery

### `get_filtered_services`

**Endpoint:** `yawlit_automotive_services.api.customer_portal.get_filtered_services`
**File:** `api/customer_portal.py`

**Purpose:**
Fetches the list of available service packages based on user selection filters.

**Parameters:**

* `category` (str): e.g., "Car Wash", "Detailing".
* `frequency_type` (str): e.g., "One Time", "Subscription".
* `vehicle_type` (str): e.g., "Hatchback", "SUV".

**Logic Highlights:**

* Filters `ProductService` doctype where `active=1`.
* Applies filters for category and frequency.
* Performs post-query filtering for `vehicle_type` (matches specific type or "All Types").
* **Crucial:** Fetches `included_addons` (from `ProductServiceAddon` child table) for each service and embeds them in the response.

**Return Structure:**

```json
{
    "success": true,
    "services": [
        {
            "name": "SRV-001",
            "product_name": "Premium Wash",
            "base_price": 499.0,
            "included_addons": [
                 {"addon": "ADD-001", "addon_name": "Interior Vacuum", "unit_price": 0}
            ],
            ...
        }
    ],
    "count": 1
}
```

---

## 2. Add-on Management

### `get_optional_addons`

**Endpoint:** `yawlit_automotive_services.api.booking.get_optional_addons`
**File:** `api/booking.py`

**Purpose:**
Retrieves a list of **optional** add-ons for a specific service (products that are *not* already included).

**Parameters:**

* `product_id` (str): The ID (`name`) of the selected `ProductService`.

**Logic Highlights:**

* Fetches the list of **included** add-on IDs for the given `product_id`.
* Fetches **all** active `AddOn` records.
* **Filtering:** Loops through all add-ons and excludes those present in the "included" list.
* **Resource Check:** Checks `resource_requirements` for each add-on to flag `requires_water` or `requires_electricity`.

**Return Structure:**

```json
{
    "success": true,
    "optional_addons": [
        {
            "name": "ADD-005",
            "addon_name": "Wax Polish",
            "unit_price": 199.0,
            "requires_water": false,
            "requires_electricity": true
        }
    ],
    "product_name": "Premium Wash"
}
```

---

## 3. Slot Availability

### `get_available_slots_enhanced`

**Endpoint:** `yawlit_automotive_services.api.booking.get_available_slots_enhanced`
**File:** `api/booking.py`

**Purpose:**
Provides an **aggregated** view of available time slots for a specific date, summing up capacity across multiple vendors/slots.

**Parameters:**

* `date_str` (str): YYYY-MM-DD format.
* `product_id` (str, optional): Currently unused in logic but present in signature.

**Logic Highlights:**

* **Validation:** Rejects past dates.
* **Aggregation:** Queries `BookingSlot` table. Groups by `start_time` and `end_time`.
* **Capacity Logic:** Sums `capacity` and `booked_count` to calculate `total_available`.
* **Vendor Check:** Iterates through individual slots to ensure at least one specific vendor-slot has capacity (`>0`).
* **Expiration:** Filters out slots where `end_time` has already passed (for "today").

**Return Structure:**

```json
{
    "success": true,
    "slots": [
        {
            "name": "SLOT-001-VENDOR-A",
            "slot_id": "09:00-10:00",
            "display_text": "9:00 AM - 10:00 AM",
            "available_capacity": 3,
            "vendor_count": 5
        }
    ]
}
```

### `check_slot_availability`

**Endpoint:** `yawlit_automotive_services.api.booking.check_slot_availability`
**File:** `api/booking.py`

**Purpose:**
Performs a final, atomic check on a specific slot ID just before booking to prevent race conditions.

**Parameters:**

* `slot_id` (str): The specific `BookingSlot` record name (e.g., `SLOT-2025-12-25-0900-V1`).

**Logic Highlights:**

* Uses `FOR UPDATE` (implied by context, though explicit SQL locking might vary) to lock the row.
* Returns `true` if `available_capacity > 0`.

---

## 4. Pricing Engine

### `calculate_booking_price`

**Endpoint:** `yawlit_automotive_services.api.booking.calculate_booking_price`
**File:** `api/booking.py`

**Purpose:**
Calculates the final booking amount, including base service, add-ons, and resource surcharges.

**Parameters:**

* `product_id` (str): Selected service.
* `addon_ids` (str/JSON): Array of selected add-on objects `[{addon: "ID", quantity: 1}]`.
* `electricity_provided` (int): 1 if customer provides, 0 if vendor needs to bring.
* `water_provided` (int): 1 if customer provides, 0 if vendor needs to bring.
* `payment_mode` (str): "Pay Now" or "Pay After Service".

**Logic Highlights:**

* **Base Price:** Fetched from `ProductService`.
* **Add-ons:** Iterates through `addon_ids`, looks up live prices from `AddOn` table (security check), and sums them (`unit_price * quantity`).
* **Surcharges:**
  * Checks product's `resource_dependency_flags` (strings "water", "electricity").
  * If dependency exists AND customer provides = 0, adds surcharge (default ₹150 from `PricingRules`).
* **Markup/Convenience Fee:** Currently hardcoded to **0** (disabled).

**Return Structure:**

```json
{
    "success": true,
    "base_price": 499.0,
    "addons_total": 199.0,
    "total_surcharges": 150.0,
    "total_amount": 848.0
}
```

---

## 5. Booking Creation & Payment

### `create_booking`

**Endpoint:** `yawlit_automotive_services.api.booking.create_booking`
**File:** `api/booking.py`

**Purpose:**
The primary transactional API. Creates the `Booking` record in the database.

**Parameters:**

* `product_id`, `booking_date`, `slot_id` (BookingSlot Name), `vehicle_id`.
* `electricity_provided`, `water_provided` (Integers).
* `addon_ids` (JSON).
* `payment_mode`.
* `payment_screenshot` (URL string, optional).

**Logic Highlights:**

* **Validation:** Checks existence of Customer Profile and required fields.
* **Creation:** Inserts a new `Booking` document.
  * Status: `'Confirmed'` (Assumes availability checked).
  * Payment Status: `'Pending'`.
* **Child Table:** Populates `add_ons_selected` child table with selected add-on details.
* **Error Handling:** specifically catches "slot unavailable" errors to return a friendly message to the user.

### `confirm_payment_and_sync_calendar`

**Endpoint:** `yawlit_automotive_services.api.booking.confirm_payment_and_sync_calendar`
**File:** `api/booking.py`

**Purpose:**
Called by the system *after* a successful "Pay Now" transaction (or manual confirmation).

**Logic Highlights:**

* Updates Booking `payment_status` to `'Partially Paid'`.
* **Invoice Generation:** Auto-generates a Frappe `Invoice` document linked to the booking (includes line items for service, addons, surcharges).
* **Calendar Sync:** Enqueues a background job (`create_calendar_event`) to sync with the customer's Google Calendar if enabled.
