package jpamb.cases.advanced;

import jpamb.utils.*;

/**
 * ADVANCED: CWE-502 Deserialization of Untrusted Data.
 */
public class CWE502 {

    // ---------------------------------------------------------
    // SINK
    // ---------------------------------------------------------

    public static void canary() {
        throw new AssertionError("Vulnerability Reached: Canary Loaded!");
    }

    // ---------------------------------------------------------
    // MOCK DESERIALIZATION
    // ---------------------------------------------------------

    private static final String EXPECTED_HEADER = "SER";

    public static String simulateResolveClassName(String payload) throws Exception {
        String[] parts = payload.split("\\|", -1);

        if (parts.length != 3) {
            throw new IllegalArgumentException("Malformed payload: must be format header|classname|params");
        }

        if (!EXPECTED_HEADER.equals(parts[0])) {
            throw new IllegalArgumentException("Invalid header");
        }

        String className = parts[1];
        if (className == null || className.isEmpty()) {
            throw new IllegalArgumentException("Class name cannot be empty");
        }

        return className;
    }

    public static Object simulateReadObject(String payload) throws Exception {
        String className = simulateResolveClassName(payload);
        String[] parts = payload.split("\\|", -1);
        String params = parts[2];

        if (className.equals("DummyButton")) {
            if (!params.isEmpty()) throw new IllegalArgumentException("DummyButton expects no params");
            return new DummyButton();
        }
        else if (className.equals("SafeCommand")) {
            if (!params.isEmpty()) throw new IllegalArgumentException("SafeCommand expects no params");
            return new SafeCommand();
        }
        else if (className.equals("__CANARY__Command")) {
            if (!params.isEmpty()) throw new IllegalArgumentException("__CANARY__Command expects no params");
            return new __CANARY__Command();
        }
        else if (className.equals("UpdatedLibrary")) {
            if (!params.isEmpty()) throw new IllegalArgumentException("UpdatedLibrary expects no params");
            return new UpdatedLibrary();
        }
        else if (className.equals("DownGradableLibrary")) {
            if (params.isEmpty()) throw new IllegalArgumentException("DownGradableLibrary expects 1 parameter (legacy flag)");

            try {
                int legacy = Integer.parseInt(params);
                return new DownGradableLibrary(legacy);
            } catch (NumberFormatException e) {
                throw new IllegalArgumentException("DownGradableLibrary parameter must be an integer");
            }
        }

        throw new ClassNotFoundException("Invalid class: " + className);
    }

    // ---------------------------------------------------------
    // CLASSES (GADGET CHAINS AND SINKS)
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

    public static class DummyButton {
        public DummyButton() {}
    }

    public static class NotMaintainedDependency {
        public NotMaintainedDependency() {
            new __CANARY__Command();
        }
    }

    public static class UpdatedLibrary {
        public UpdatedLibrary() {
            new NotMaintainedDependency();
        }
    }

    public static class DownGradableLibrary {
        private int legacy = 0;
        public DownGradableLibrary(int legacy) {
            this.legacy = legacy;
            if (legacy == 1) {
                new NotMaintainedDependency();
            }
        }
    }

    // ---------------------------------------------------------
    // CASES
    // ---------------------------------------------------------

    @Case("(s'SER|DummyButton|') -> ok")
    @Case("(s'SER|SafeCommand|') -> ok")
    @Case("(s'SER|__CANARY__Command|') -> assertion error")
    public static void insecure_deserialization(String serializedPayload) {
        try {
            Object deserializedObj = simulateReadObject(serializedPayload);

            DummyButton button = (DummyButton) deserializedObj;

        } catch (Exception e) {
            return;
        }
    }

    @Case("(s'SER|DummyButton|') -> ok")
    @Case("(s'SER|__CANARY__Command|') -> ok")
    @Case("(s'SER|UpdatedLibrary|') -> assertion error")
    public static void blacklist_deserialization(String serializedPayload) {
        try {
            String[] blacklist = new String[] { "__CANARY__Command", "SafeWrapperCommand" };
            String className = simulateResolveClassName(serializedPayload);
            for (String blacklisted : blacklist) {
                if (className.contains(blacklisted)) {
                    return;
                }
            }
            Object deserializedObj = simulateReadObject(serializedPayload);

            DummyButton button = (DummyButton) deserializedObj;

        } catch (Exception e) {
            return;
        }
    }

    @Case("(s'SER|__CANARY__Command|') -> ok")
    @Case("(s'SER|DownGradableLibrary|0') -> ok")
    @Case("(s'SER|DownGradableLibrary|1') -> assertion error")
    public static void whitelist_deserialization(String serializedPayload) {
        try {
            String[] whitelist = new String[] { "DownGradableLibrary" };
            String className = simulateResolveClassName(serializedPayload);
            boolean allowed = false;
            for (String whitelisted : whitelist) {
                if (className.equals(whitelisted)) {
                    allowed = true;
                }
            }
            if (!allowed) {
                return;
            }
            Object deserializedObj = simulateReadObject(serializedPayload);

            DownGradableLibrary library = (DownGradableLibrary) deserializedObj;

        } catch (Exception e) {
            return;
        }
    }
}
