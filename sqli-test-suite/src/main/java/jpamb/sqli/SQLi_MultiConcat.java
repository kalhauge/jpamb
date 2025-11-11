package jpamb.sqli;

public class SQLi_MultiConcat {
    // VULNERABLE
    public static void vulnerable(String table, String column, String value) {
        String query = "SELECT " + column + " FROM " + table + " WHERE id = " + value;
        executeQuery(query);
    }
    
    // SAFE
    public static void safe(String value) {
        String sanitized = value.replaceAll("[^0-9]", "");
        String query = "SELECT name FROM users WHERE id = " + sanitized;
        executeQuery(query);
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
