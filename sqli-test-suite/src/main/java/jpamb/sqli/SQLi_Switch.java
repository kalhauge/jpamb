package jpamb.sqli;

public class SQLi_Switch {
    // VULNERABLE
    public static void vulnerable(String input, int option) {
        String query;
        switch (option) {
            case 1:
                query = "SELECT * FROM users WHERE id = " + input;
                break;
            case 2:
                query = "SELECT * FROM admins WHERE id = " + input;
                break;
            default:
                query = "SELECT * FROM guests WHERE id = " + input;
        }
        executeQuery(query);
    }
    
    // SAFE
    public static void safe(int option) {
        String query;
        switch (option) {
            case 1:
                query = "SELECT * FROM users WHERE id = 42";
                break;
            case 2:
                query = "SELECT * FROM admins WHERE id = 43";
                break;
            default:
                query = "SELECT * FROM guests WHERE id = 1";
        }
        executeQuery(query);
    }
    
    private static void executeQuery(String q) {
        System.out.println("Executing: " + q);
    }
}
