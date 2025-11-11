package jpamb.sqli;

public class SQLi_StringBuffer {
    // VULNERABLE
    public static void vulnerable(String[] inputs) {
        StringBuffer sb = new StringBuffer("SELECT * FROM users WHERE id IN (");
        for (String input : inputs) {
            sb.append(input).append(", ");
        }
        sb.append(")");
        String query = sb.toString();
        executeQuery(query);
    }
    
    // SAFE
    public static void safe() {
        StringBuffer sb = new StringBuffer("SELECT * FROM users WHERE id IN (");
        String[] ids = {"1", "2", "3"};
        for (String id : ids) {
            sb.append(id).append(", ");
        }
        sb.append(")");
        String query = sb.toString();
        executeQuery(query);
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
