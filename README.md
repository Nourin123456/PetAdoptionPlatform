# 🐾 DreamlyPaws - Pet Adoption Platform

A full-stack Flask and SQLite web application designed to connect prospective adopters with rescue animals and verified animal shelters. The platform streamlines the complete adoption lifecycle—from initial browsing and pet inquiry submission, through transparent fixed-fee payment verification, to direct shelter-managed delivery scheduling and live transport milestone tracking.

---

## 📌 Project Abstract

The **Pet Adoption Platform (DreamlyPaws)** provides a centralized, secure digital ecosystem facilitating ethical pet adoptions. Recognizing that animal welfare organizations require close operational oversight over pet placement and logistical safety, the platform architecture consolidates all delivery and transport coordination directly under the **Shelter Module**, completely eliminating the need for an independent third-party transport provider role.

Adopters browse verified pet listings with complete vaccination and health records, submit structured adoption inquiries, select their preferred delivery method (*Home Delivery* or *Shelter Pickup*), and complete payment through secure UPI or Cash on Delivery. Shelters maintain complete administrative control over their rescue profiles, review adoption applications, inspect adopter delivery preferences, schedule delivery/handover dates, and update real-time transit milestones (*Pending*, *Scheduled*, *In Transit*, *Delivered*). Platform administrators oversee shelter accreditation, audit pet listings, and ensure system integrity.

---

## 🏛️ System Architecture & Core Modules

The system is organized into **six core functional modules**:

```
+-----------------------------------------------------------------------------------+
|                           PET ADOPTION PLATFORM                                   |
+---------------------+-------------------------------+-----------------------------+
|  1. ADOPTER MODULE  |      2. SHELTER MODULE        |      ADMINISTRATION         |
|  - Registration/Auth|  - Shelter Verification & Auth|  - Shelter Approvals        |
|  - Search & Filter  |  - Dashboard & Operations Hub |  - Pet Listing Oversight    |
|  - Inquiries & Chat |  - Shelter Profile Management |  - Platform Audit & Messages|
|  - Request Tracking |                               |                             |
+---------------------+-------------------------------+-----------------------------+
|                                  CORE SERVICES                                    |
+----------------------------+-------------------------------+----------------------+
| 3. PET MANAGEMENT          | 4. ADOPTION MANAGEMENT        | 5. PAYMENT MANAGEMENT|
| - Photo & Cropping Tools   | - Request Review Pipeline     | - Flat ₹500 Fee      |
| - Vaccination Status       | - Approval / Rejection Logic  | - UPI QR Integration |
| - Breed, Age & Description | - Status Transition Records   | - Pay on Delivery/COD|
+----------------------------+-------------------------------+----------------------+
|             6. DELIVERY & TRANSPORT MANAGEMENT (UNDER SHELTER MODULE)             |
| - Adopter Delivery Selection ('Home Delivery' vs 'Shelter Pickup' - Immutable)    |
| - Shelter Delivery Date Scheduling & Rescheduling                                 |
| - Transport Status Progression (Pending -> Scheduled -> In Transit -> Delivered)  |
| - Delivery Handover Logistics & Destination Overview                              |
+-----------------------------------------------------------------------------------+
```

### 1. Adopter Module
* Account registration and secure authentication.
* Browse and search available pets by keyword, category (dog, cat, rabbit, etc.), and breed.
* Submit formal adoption applications with contact and address information.
* Select delivery preference (*Home Delivery* or *Shelter Pickup*) at the time of request submission.
* Track application approval state, scheduled handover date, and live delivery status.
* Direct messaging with administration and shelters for adoption support.

### 2. Shelter Module
* Registration with mandatory administrator review and approval.
* Centralized Shelter Dashboard providing real-time statistics, pending requests, listed pets, and delivery operations.
* Organization profile maintenance (headquarters address, phone, contact credentials).

### 3. Pet Management
* Creation, editing, and deletion of rescue pet listings.
* Automated client-side face framing and server-side image aspect ratio cropping.
* Comprehensive metadata tracking (breed, age, gender, vaccination record, behavioral description).
* Real-time availability tracking (*Available* vs *Adopted*).

### 4. Adoption Management
* Shelter application review pipeline (inspect adopter details, living environment, and delivery choice).
* Decision workflow:
  * **Approve**: Locks adoption, updates pet status to *Adopted*, schedules delivery date, sets transport status to *Scheduled*.
  * **Reject**: Reopens pet listing to *Available*, flags refund status where applicable.

### 5. Payment Management
* Transparent, non-negotiable flat adoption fee of **₹500**.
* Dual payment methods:
  * **UPI**: Deep-linked UPI IDs, validation, transaction date logging, and printable payment confirmation cards.
  * **Cash on Delivery (COD)**: Payment collected at delivery handover.

### 6. Delivery / Transport Management (Under Shelter)
* **Adopter Delivery Selection**: The adopter selects *Home Delivery* or *Shelter Pickup* during the initial application. **The Shelter cannot change the adopter's selected delivery method.**
* **Delivery Scheduling**: Upon adoption approval, the Shelter sets the scheduled delivery/handover date.
* **Rescheduling**: The Shelter can adjust or reschedule the delivery date at any time with automated validation.
* **Live Status Milestones**: The Shelter updates transit milestones:
  * `Pending`: Initial state awaiting request review and approval.
  * `Scheduled`: Delivery/pickup date confirmed by shelter.
  * `In Transit`: Pet dispatched for home delivery or en route.
  * `Delivered`: Pet successfully handed over to adopter.
* **Adopter Visibility**: Adopters track live status and scheduled dates in real time without third-party transport provider accounts.

---

## 👥 System Actors & Roles

| Role | Description | Core Capabilities |
| :--- | :--- | :--- |
| **Adopter** | General public looking to adopt | Register, browse pets, submit adoption requests, choose delivery method, pay ₹500 fee, view live transport status. |
| **Shelter** | Animal shelters and rescue sanctuaries | Manage pets, review applications, schedule delivery dates, reschedule dates, update transport statuses, manage handovers. |
| **Administrator** | Platform compliance and oversight | Approve/reject shelter registrations, audit pet listings, monitor adoption inquiries, system messaging. |

> **Note on Architecture Consistency**: There is **no separate Transport Provider role or module**. All logistics, handover coordination, and transport status workflows are integrated directly within the **Shelter Module**.

---

## 🗄️ Database Schema Overview

The SQLite database (`database.db`) consists of four primary relational tables:

1. **`users`**: User credentials and roles (`Adopter`, `Shelter`, `Admin`), contact info, address, and account status (`Pending`, `Approved`, `Active`).
2. **`pets`**: Animal profile data (`name`, `breed`, `age`, `gender`, `vaccinated`, `description`, `image`, `status`, `shelter_id`).
3. **`adoptions`**: Adoption records connecting pets, adopters, and shelters:
   * `pet_id`, `adopter_id`, `adopter_name`, `phone`, `address`
   * `request_status` (`Pending`, `Approved`, `Rejected`)
   * `payment_status` (`Pending`, `Paid`, `COD`), `payment_method`, `payment_amount` (₹500), `upi_id`, `payment_date`
   * `transport_method` (`Home Delivery`, `Shelter Pickup` - chosen by adopter)
   * `transport_date`, `transport_time` (managed by shelter)
   * `transport_status` (`Pending`, `Scheduled`, `In Transit`, `Delivered` - managed by shelter)
4. **`messages`**: Support and contact inquiries between users, shelters, and administration.

---

## 🚀 Getting Started

### Prerequisites
* Python 3.9+
* SQLite3

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Nourin123456/PetAdoptionPlatform.git
   cd PetAdoptionPlatform
   ```

2. **Install dependencies:**
   ```bash
   pip install flask werkzeug pillow
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Access the platform:**
   Open your browser and navigate to `http://127.0.0.1:5000/`.

### Default Accounts

* **Administrator**:
  * Email: `admin@petadoption.com`
  * Password: `admin123`
* **Sample Shelter**:
  * Register via `/register` (select *Shelter / Sanctuary*) and approve via the Admin portal.

---

## 📊 UML & Architecture Diagrams

Comprehensive Data Flow Diagrams (DFDs) and UML Use Case Diagrams reflecting the 3-actor architecture are available in the [`dfd_diagrams/`](dfd_diagrams/) directory:
* **Context Diagram (DFD Level 0)**: High-level data flows between Adopter, Shelter, and Administrator.
* **DFD Level 1**: Subsystem decompositions for Shelter Operations (Pet listings, request approvals, delivery dispatching), Adopter Workflows, and Administrator oversight.
* **UML Use Case Diagrams**: Actor boundary interactions mapping use cases to Adopter, Shelter, and Admin.
