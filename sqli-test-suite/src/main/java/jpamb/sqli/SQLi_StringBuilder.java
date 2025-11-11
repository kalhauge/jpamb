package jpamb.sqli;

public class SQLi_StringBuilder {
    // VULNERABLE
    public static void vulnerable(String input) {
        StringBuilder sb = new StringBuilder();
        sb.append("SELECT * FROM users WHERE id = ");
        sb.append(input);
        String query = sb.toString();
        executeQuery(query);
    }
    
    // SAFE
    public static void safe() {
        StringBuilder sb = new StringBuilder();
        sb.append("SELECT * FROM users WHERE id = ");
        sb.append("42");
        String query = sb.toString();
        executeQuery(query);
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
