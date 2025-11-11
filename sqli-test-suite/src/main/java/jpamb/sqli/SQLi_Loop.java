package jpamb.sqli;

public class SQLi_Loop {
    // VULNERABLE
    public static void vulnerable(String[] inputs) {
        String query = "SELECT * FROM users WHERE id IN (";
        for (int i = 0; i < inputs.length; i++) {
            query += inputs[i];
            if (i < inputs.length - 1) query += ", ";
        }
        query += ")";
        executeQuery(query);
    }
    
    // SAFE
    public static void safe() {
        String query = "SELECT * FROM users WHERE id IN (";
        String[] ids = {"42", "43", "44"};
        for (int i = 0; i < ids.length; i++) {
            query += ids[i];
            if (i < ids.length - 1) query += ", ";
        }
        query += ")";
        executeQuery(query);
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
