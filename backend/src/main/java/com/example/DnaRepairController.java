package com.example;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * ============================================================
 * DNA Repair API Controller (MitoSeqFix Backend Interface)
 * ============================================================
 *
 * This REST controller exposes the DNA repair pipeline as a
 * web-accessible service.
 *
 * It acts as the entry point between:
 *   • Frontend (React UI)
 *   • Backend ML inference service (Python model pipeline)
 *
 * Responsibilities:
 *   - Input validation
 *   - Request routing
 *   - Error handling
 *   - Service delegation
 */
@RestController
@CrossOrigin(origins = "http://localhost:3000")
@RequestMapping("/api")
public class DnaRepairController {

    /**
     * Service layer encapsulating ML inference logic.
     * The controller does not perform computation directly,
     * ensuring separation of concerns.
     */
    @Autowired
    private DnaRepairService service;

    /**
     * ============================================================
     * DNA Repair Endpoint
     * ============================================================
     *
     * Endpoint: POST /api/repair
     *
     * Input:
     *   JSON object containing raw DNA sequence
     *
     * Output:
     *   RepairResponse containing:
     *     - repaired DNA sequence
     *     - mutation statistics
     *     - confidence score
     *
     * The endpoint forwards the raw sequence to the ML pipeline,
     * which handles encoding, prediction, and reconstruction.
     */
    @PostMapping("/repair")
    public ResponseEntity<RepairResponse> repairDna(
            @RequestBody DnaRequest request) {

        try {

            // ----------------------------------------------------
            // Input validation (ensures model safety & stability)
            // ----------------------------------------------------
            if (request == null ||
                    request.getSequence() == null ||
                    request.getSequence().isBlank()) {

                return ResponseEntity.badRequest()
                        .body(new RepairResponse(
                                "Error: Sequence is missing"
                        ));
            }

            // ----------------------------------------------------
            // Delegate to ML-backed repair service
            // Note: Full sequence is passed including ambiguity
            // markers (N bases), handled internally by model
            // ----------------------------------------------------
            RepairResponse response = service.repair(
                    request.getSequence()
            );

            return ResponseEntity.ok(response);

        } catch (Exception e) {

            // ----------------------------------------------------
            // Global exception handling for API stability
            // Prevents raw stack traces leaking to frontend
            // ----------------------------------------------------
            return ResponseEntity.internalServerError()
                    .body(new RepairResponse(
                            "Error: " + e.getMessage()
                    ));
        }
    }
}