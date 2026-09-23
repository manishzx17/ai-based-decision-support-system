# Database Documentation - 12C Decision Support System

## Relational Schema (PostgreSQL / SQLite)

The database schema consists of 18 tables:

1. `users`: User authentication, full name, role, timestamp.
2. `patient_profiles`: Patient age, gender, blood group, allergies, chronic conditions, current city, emergency contact.
3. `medical_reports`: Uploaded report file details, OCR raw text, summary, recommended specialty, status.
4. `extracted_entities`: Biomedical NER entities (Disease, Symptom, Medication, Procedure, BodyPart), confidence, context snippet.
5. `hospitals`: Hospital metadata, city, address, latitude/longitude, specialties, rating, distance, insurance accepted, facilities.
6. `doctors`: Doctor qualifications, specialty, experience years, rating, consultation fee, availability.
7. `pharmacies`: 24/7 pharmacy directory, address, location, medication stock summary.
8. `treatment_costs`: Hospital procedure cost ranges (min_cost, max_cost, avg_cost, room_type).
9. `insurance_providers`: Insurance policy details, network hospital count, TPA contact.
10. `appointments`: Digital appointment bookings, patient name, doctor ID, date, time, status.
11. `accommodations`: Patient hotel stays, price per night, distance to hospital, wheelchair facilities.
12. `emergency_contacts`: City emergency numbers, trauma centers, blood banks, ambulance dispatch.
13. `travel_plans`: Patient travel itineraries, destination city, duration, itinerary JSON, cost estimate.
14. `conversations`: AI Assistant chat threads.
15. `chat_messages`: Multi-turn chat message history, sender, content, timestamp.
16. `medical_knowledge`: Grounded clinical guidelines database for RAG keyword & vector search.
