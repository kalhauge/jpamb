package jpamb.cases.advanced;

import jpamb.utils.*;

/**
 * ADVANCED: CWE-470 Unsafe Reflection (use of externally-controlled input
 * to select classes or code).
 */
public class CWE470 {

    // ---------------------------------------------------------
    // SINK
    // ---------------------------------------------------------

    public static void canary() {
        throw new AssertionError("Vulnerability Reached: Canary Loaded!");
    }

    // ---------------------------------------------------------
    // DEPENDENCIES
    // ---------------------------------------------------------

    public static class __CANARY__Command {
        public __CANARY__Command() {
            canary();
        }
    }

    public static class SafeCommand {
        public void doAction() {
            return;
        }
    }

    public static class SafeWrapperCommand extends __CANARY__Command {}

    // ---------------------------------------------------------
    // CASES
    // ---------------------------------------------------------

    @Case("(s'Safe') -> ok")
    @Case("(s'__CANARY__') -> assertion error")
    public static void unsafe_dispatcher(String ctl) {
        String className = "jpamb.cases.advanced.CWE470$" + ctl + "Command";

        try {
            Class<?> cmdClass = Class.forName(className);
            SafeCommand ao = (SafeCommand) cmdClass.newInstance();

            ao.doAction();

        } catch (Exception e) {
            return;
        }
    }

    @Case("(s'Safe') -> ok")
    @Case("(s'SafeWrapper') -> assertion error")
    public static void weak_dispatcher(String ctl) {

        if (!ctl.startsWith("Safe")) {
            return;
        }

        String className = "jpamb.cases.advanced.CWE470$" + ctl + "Command";

        try {
            Class<?> cmdClass = Class.forName(className);
            SafeCommand ao = (SafeCommand) cmdClass.newInstance();
            ao.doAction();
        } catch (Exception e) {
            return;
        }
    }

    @Case("(s'Any') -> ok")
    public static void strict_safe_dispatcher(String ctl) {

        if (!"Safe".equals(ctl)) {
            return;
        }

        String className = "jpamb.cases.advanced.CWE470$" + ctl + "Command";

        try {
            Class<?> cmdClass = Class.forName(className);
            SafeCommand ao = (SafeCommand) cmdClass.newInstance();
            ao.doAction();
        } catch (Exception e) {
            return;
        }
    }
}
