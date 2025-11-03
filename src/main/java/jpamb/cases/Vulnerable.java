package jpamb.cases;

import jpamb.utils.Case;

public class Vulnerable {

  private final MySQLEngine mysql;

  public Vulnerable() {
    this.mysql = new MySQLEngine();
  }

  // === 1. Simple tainted flow ===
  // The username and password come directly from the user and are concatenated
  // into the query string. A taint analysis should flag this.
  @Case("('john', 'password') -> tainted")
  @Case("('admin' OR 1=1, '') -> tainted")
  public void simpleTainted(String username, String password) {
    String query = "SELECT * FROM users WHERE username=" + username +
                   " AND password=" + password + ";";

    // SINK
    mysql.executeQuery(query);
  }

  // === 2. Not tainted ===
  // Query is fully constant, not influenced by user input.
  @Case("('anything', 'else') -> not tainted")
  public void simpleClean(String username, String password) {
    String query = "SELECT * FROM users WHERE username='john' AND password='password';";

    // SINK
    mysql.executeQuery(query);
  }

  // === 3. Input validated before use (not tainted in sink) ===
  // Input is checked strictly before being used in a constant query.
  @Case("('john', 'password') -> not tainted")
  @Case("(admin' OR 1=1--, '') -> not tainted")
  public void validatedSafe(String username, String password) {
    String query = "";

    if (username.equals("john") && password.equals("password")) {
      query = "SELECT * FROM users WHERE username='john' AND password='password';";
    }

    // SINK
    mysql.executeQuery(query);
  }

  // === 4. SQL injection (subset of tainted) ===
  // This case uses direct concatenation *and* injection content.
  // The analysis should flag it as tainted, and possibly also classify as SQL injection.
  @Case("(admin' OR 1=1--, '') -> sql injection")
  public void sqlInjection(String username, String password) {
    String query = "SELECT * FROM users WHERE username='" + username +
                   "' AND password='" + password + "';";

    // SINK
    mysql.executeQuery(query);
  }

  // === Dummy Sink Implementation ===
  // The sink itself does nothing meaningful.
  private static class MySQLEngine {
    public void executeQuery(String query) {
      // This is the sink the taint analysis should detect
      // whether 'query' depends on untrusted input or not.
    }
  }
}
