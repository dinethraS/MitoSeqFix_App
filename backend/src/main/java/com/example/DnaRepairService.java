package com.example;

import org.springframework.stereotype.Service;
import java.io.*;

@Service
public class DnaRepairService {
    public String repair(String dna) throws Exception {
        ProcessBuilder pb = new ProcessBuilder(
                "D:\\FYP\\MitoSeqFix_App\\mtDNA_env\\Scripts\\python.exe",
                "D:\\FYP\\MitoSeqFix_App\\python_model\\repair_single_seq.py"
        );
        pb.directory();

        Process process = pb.start();

        BufferedWriter writer =
                new BufferedWriter(new OutputStreamWriter(process.getOutputStream()));

        writer.write(dna);
        writer.flush();
        writer.close();

        BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));

        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            sb.append(line.trim());
        };

        BufferedReader errorReader =
                new BufferedReader(new InputStreamReader(process.getErrorStream()));

        String err;
        while ((err = errorReader.readLine()) != null) {
            System.out.println("PYTHON ERROR: " + err);
        }

        String result = sb.toString();

        process.waitFor();

        return result;
    }
}
