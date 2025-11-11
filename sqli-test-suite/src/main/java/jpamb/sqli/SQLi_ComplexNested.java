package jpamb.sqli;

public class SQLi_ComplexNested {
    // VULNERABLE
    public static void vulnerable(String input) {
        String trimmed = input.trim();
        String upper = trimmed.toUpperCase();
        String[] parts = upper.split(" ");
        String first = parts.length > 0 ? parts[0] : "";
        String escaped = first.replace("'", "''");
        
        String query = "SELECT * FROM users WHERE name = '" + escaped + "'";
        executeQuery(query);
    }
    
    // SAFE
    public static void safe() {
        String input = "  admin user  ";
        String trimmed = input.trim();
        String upper = trimmed.toUpperCase();
        String[] parts = upper.split(" ");
        String first = parts[0];
        
        String query = "SELECT * FROM users WHERE name = '" + first + "'";
        executeQuery(query);
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
