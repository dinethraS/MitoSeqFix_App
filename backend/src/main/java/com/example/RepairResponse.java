package com.example;

public class RepairResponse {
    private String repaired;
    private boolean success;
    private int inputLen;
    private int outputLen;
    private int changes;  // int not long

    public RepairResponse(String repaired, boolean success, int inputLen, int outputLen, int changes) {
        this.repaired = repaired;
        this.success = success;
        this.inputLen = inputLen;
        this.outputLen = outputLen;
        this.changes = changes;
    }

    // Getters ONLY (no setters needed)
    public String getRepaired() { return repaired; }
    public boolean isSuccess() { return success; }
    public int getInputLen() { return inputLen; }
    public int getOutputLen() { return outputLen; }
    public int getChanges() { return changes; }
}