package com.example;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@CrossOrigin(origins = "http://localhost:3000")
@RequestMapping("/api")
public class DnaRepairController {

    @Autowired
    private DnaRepairService service;

    @PostMapping("/repair")
    public ResponseEntity<RepairResponse> repairDna(@RequestBody DnaRequest request) {
        try {
            String input = request.getSequence();
            String output = service.repair(input);

            int inputLen = input.length();
            int outputLen = output.length();
            int changes = 0;
            int minLen = Math.min(inputLen, outputLen);
            for (int i = 0; i < minLen; i++) {
                if (input.charAt(i) != output.charAt(i)) changes++;
            }

            return ResponseEntity.ok(new RepairResponse(output, true, inputLen, outputLen, changes));
        } catch(Exception e) {
            return ResponseEntity.badRequest()
                    .body(new RepairResponse("Error: " + e.getMessage(), false, 0, 0, 0));
        }
    }
}
