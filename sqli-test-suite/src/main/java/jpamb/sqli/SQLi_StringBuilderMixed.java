package jpamb.sqli;

public class SQLi_StringBuilderMixed {
    // VULNERABLE
    public static void vulnerable(String input) {
        StringBuilder sb = new StringBuilder();
        sb.append("SELECT * FROM ");
        sb.append("users");
        sb.append(" WHERE name = '");
        sb.append(input);
        sb.append("'");
        String query = sb.toString();
        executeQuery(query);
    }
    
    // SAFE
    public static void safe() {
        StringBuilder sb = new StringBuilder();
        sb.append("SELECT * FROM ");
        sb.append("users");
        sb.append(" WHERE id = ");
        sb.append("42");
        String query = sb.toString();
        executeQuery(query);
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
