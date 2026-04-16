package com.example;

/**
 * ============================================================
 * DNA Request DTO (Data Transfer Object)
 * ============================================================
 *
 * This class represents the input payload sent from the
 * frontend to the backend REST API.
 *
 * It is used as a lightweight container for transferring
 * DNA sequence data without any business logic.
 *
 * Design Rationale:
 *   - Separates API data representation from internal models
 *   - Ensures clean deserialization from JSON (Spring Boot)
 *   - Keeps controller layer decoupled from raw input handling
 */
public class DnaRequest {

    /**
     * Raw DNA sequence submitted by the user.
     *
     * Expected format:
     *   String containing A, T, C, G, and optional N bases
     */
    private String sequence;

    /**
     * Default constructor required by Spring Boot
     * for JSON deserialization.
     */
    public DnaRequest() {}

    /**
     * Returns the DNA sequence provided in the request.
     */
    public String getSequence() {
        return sequence;
    }

    /**
     * Sets the DNA sequence during request parsing.
     */
    public void setSequence(String sequence) {
        this.sequence = sequence;
    }
}