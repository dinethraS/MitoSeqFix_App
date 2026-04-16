package com.example;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;

import java.io.*;
import java.util.concurrent.*;

/**
 * ============================================================
 * DNA Repair Service (Python ML Integration Layer)
 * ============================================================
 *
 * This service acts as the bridge between the Java backend
 * (Spring Boot) and the Python-based deep learning model.
 *
 * It is responsible for:
 *   - Executing the external Python inference script
 *   - Streaming input DNA sequence to the model
 *   - Capturing model output (JSON prediction)
 *   - Handling execution errors and timeouts safely
 *
 * Architectural Role:
 *   This class enables cross-language interoperability between
 *   the REST API layer and the ML inference pipeline.
 */
@Service
public class DnaRepairService {

    // Path to Python interpreter inside virtual environment
    private static final String PYTHON_EXE =
            "D:\\FYP\\MitoSeqFix_App\\mtDNA_env\\Scripts\\python.exe";

    // Path to trained model inference script
    private static final String PYTHON_SCRIPT =
            "D:\\FYP\\MitoSeqFix_App\\python_model\\repair_single_seq.py";

    private final ObjectMapper mapper = new ObjectMapper();

    // Thread pool used to prevent blocking on IO streams
    private final ExecutorService executor = Executors.newCachedThreadPool();

    /**
     * ============================================================
     * Executes DNA repair inference using external Python process
     * ============================================================
     *
     * @param dna Raw mitochondrial DNA sequence
     * @return RepairResponse parsed from Python JSON output
     */
    public RepairResponse repair(String dna) throws Exception {

        // --------------------------------------------------------
        // Launch Python inference process
        // --------------------------------------------------------
        ProcessBuilder pb = new ProcessBuilder(PYTHON_EXE, PYTHON_SCRIPT);
        pb.redirectErrorStream(false); // keep stdout and stderr separate
        Process process = pb.start();

        // --------------------------------------------------------
        // Stream input DNA to Python process (non-blocking)
        // --------------------------------------------------------
        Future<?> stdinFuture = executor.submit(() -> {
            try (BufferedWriter writer =
                         new BufferedWriter(
                                 new OutputStreamWriter(process.getOutputStream()))) {
                writer.write(dna);
                writer.flush();
            } catch (IOException e) {
                throw new UncheckedIOException(e);
            }
        });

        // --------------------------------------------------------
        // Capture standard output (model prediction JSON)
        // --------------------------------------------------------
        Future<String> stdoutFuture = executor.submit(() -> {
            StringBuilder sb = new StringBuilder();
            try (BufferedReader reader =
                         new BufferedReader(
                                 new InputStreamReader(process.getInputStream()))) {

                String line;
                while ((line = reader.readLine()) != null) {
                    sb.append(line.trim());
                }

            } catch (IOException e) {
                throw new UncheckedIOException(e);
            }
            return sb.toString();
        });

        // --------------------------------------------------------
        // Capture error stream (Python logs / debugging info)
        // --------------------------------------------------------
        Future<String> stderrFuture = executor.submit(() -> {
            StringBuilder sb = new StringBuilder();
            try (BufferedReader reader =
                         new BufferedReader(
                                 new InputStreamReader(process.getErrorStream()))) {

                String line;
                while ((line = reader.readLine()) != null) {
                    sb.append("PYTHON: ").append(line).append("\n");
                }

            } catch (IOException e) {
                throw new UncheckedIOException(e);
            }
            return sb.toString();
        });

        // --------------------------------------------------------
        // Synchronize execution with timeout protection
        // --------------------------------------------------------
        stdinFuture.get(60, TimeUnit.SECONDS);
        String json    = stdoutFuture.get(60, TimeUnit.SECONDS);
        String errLogs = stderrFuture.get(60, TimeUnit.SECONDS);

        int exitCode = process.waitFor();

        // --------------------------------------------------------
        // Log Python errors for debugging and traceability
        // --------------------------------------------------------
        if (!errLogs.isEmpty()) {
            System.out.println(errLogs);
        }

        // --------------------------------------------------------
        // Validate execution success before parsing output
        // --------------------------------------------------------
        if (exitCode != 0 || json.isEmpty()) {
            throw new RuntimeException(
                    "Python inference failed (exit code " + exitCode + ").\n"
                            + "Error log:\n" + errLogs
            );
        }

        // --------------------------------------------------------
        // Convert JSON output into Java response object
        // --------------------------------------------------------
        return mapper.readValue(json, RepairResponse.class);
    }
}