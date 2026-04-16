package com.example;

import org.springframework.stereotype.Service;
import java.util.*;

/**
 * ============================================================
 * DamageAnalysisService
 * ============================================================
 *
 * This service implements a rule-based biological baseline
 * for mitochondrial DNA damage classification.
 *
 * It is used as:
 *   1. A pre-ML interpretability comparator
 *   2. A heuristic baseline for validation of MitoSeqFix model
 *   3. A biologically grounded scoring system for mutation types
 *
 * Unlike the neural model (which learns patterns), this module
 * explicitly encodes known mitochondrial mutation signatures.
 */
@Service
public class DamageAnalysisService {

    /**
     * Performs rule-based DNA damage analysis.
     *
     * This method approximates biological degradation using:
     *   - Transition mutations (C→T deamination)
     *   - Transversion mutations (G→T oxidation)
     *   - Sequence fragmentation (N-gaps)
     */
    public DamageReport analyze(String sequence) {

        // --------------------------------------------------------
        // 1. Preprocessing: Standardize nucleotide sequence
        // --------------------------------------------------------
        String seq = sequence.toUpperCase().replaceAll("[^ATCGN]", "");
        int total = seq.length();

        if (total == 0) {
            return new DamageReport(
                    0,
                    Collections.emptyList(),
                    "unknown"
            );
        }

        // --------------------------------------------------------
        // 2. Mutation signature detection (biological ground truth)
        // --------------------------------------------------------
        int ctTransitions = 0;     // C→T deamination signature
        int gtTransversions = 0;   // G→T oxidative damage signature

        for (int i = 0; i < seq.length() - 1; i++) {
            char a = seq.charAt(i);
            char b = seq.charAt(i + 1);

            if (a == 'C' && b == 'T') ctTransitions++;
            if (a == 'G' && b == 'T') gtTransversions++;
        }

        // --------------------------------------------------------
        // 3. Fragmentation analysis (sequence integrity loss)
        // --------------------------------------------------------
        long nCount = seq.chars().filter(c -> c == 'N').count();
        double sparsity = (double) nCount / total;

        // Detect contiguous missing regions
        boolean hasNGaps = seq.contains("NNN");

        // Normalised biological scores
        double deaminationScore = (double) ctTransitions / total;
        double oxidationScore   = (double) gtTransversions / total;

        List<DamageType> types = new ArrayList<>();

        // --------------------------------------------------------
        // 4. Rule-based biological classification
        // --------------------------------------------------------

        // C→T deamination (most common ancient DNA damage signal)
        if (deaminationScore > 0.005) {
            types.add(new DamageType(
                    "Deamination Damage",
                    Math.min((int)(deaminationScore * 2800), 99),
                    "High frequency of C→T transition signatures."
            ));
        }

        // Fragmentation / missing base regions
        if (sparsity > 0.02 || hasNGaps) {
            types.add(new DamageType(
                    "Fragmentation / Missing Bases",
                    Math.min((int)(sparsity * 450), 99),
                    "Detected sequence gaps and missing information."
            ));
        }

        // G→T oxidative damage (base oxidation artefact)
        if (oxidationScore > 0.003) {
            types.add(new DamageType(
                    "Oxidative Damage",
                    Math.min((int)(oxidationScore * 3500), 99),
                    "G→T transversion pattern detected."
            ));
        }

        // --------------------------------------------------------
        // 5. Fallback class (no strong damage signature detected)
        // --------------------------------------------------------
        if (types.isEmpty()) {
            types.add(new DamageType(
                    "Low / No Damage",
                    95,
                    "Sequence integrity appears high."
            ));
        }

        // --------------------------------------------------------
        // 6. Overall severity scoring function
        // --------------------------------------------------------
        int score = (int) Math.min(
                (deaminationScore * 4000 +
                        oxidationScore * 3000 +
                        sparsity * 300),
                100
        );

        String severity =
                (score >= 60) ? "SEVERE" :
                        (score >= 30) ? "MODERATE" :
                                "LOW";

        return new DamageReport(score, types, severity);
    }

    /**
     * ============================================================
     * Inner class: DamageType
     * ============================================================
     *
     * Represents a single detected biological damage mechanism.
     * Each type includes:
     *   - name: biological category
     *   - confidence: heuristic confidence score (0–99)
     *   - detail: interpretability explanation
     */
    public static class DamageType {
        public String name;
        public int confidence;
        public String detail;

        public DamageType(String n, int c, String d) {
            name = n;
            confidence = c;
            detail = d;
        }
    }

    /**
     * ============================================================
     * Inner class: DamageReport
     * ============================================================
     *
     * Final structured output returned by the service.
     * Combines:
     *   - Global damage severity score
     *   - Detected mutation categories
     *   - Overall severity label
     */
    public static class DamageReport {
        public int damageScore;
        public List<DamageType> detectedTypes;
        public String severity;

        public DamageReport(int s, List<DamageType> t, String sev) {
            damageScore = s;
            detectedTypes = t;
            severity = sev;
        }
    }
}