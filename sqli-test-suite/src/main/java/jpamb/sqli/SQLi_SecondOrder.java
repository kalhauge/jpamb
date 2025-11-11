package jpamb.sqli;

public class SQLi_SecondOrder {
    // VULNERABLE
    public static void vulnerable(String username) {
        String insertQuery = "INSERT INTO users (username) VALUES ('" + username + "')";
        executeQuery(insertQuery);
        
        String selectQuery = "SELECT * FROM logs WHERE user = '" + username + "'";
        executeQuery(selectQuery);
    }
    
    // SAFE
    public static void safe() {
        String username = "admin";
        String insertQuery = "INSERT INTO users (username) VALUES ('" + username + "')";
        executeQuery(insertQuery);
        
        String selectQuery = "SELECT * FROM logs WHERE user = '" + username + "'";
        executeQuery(selectQuery);
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
