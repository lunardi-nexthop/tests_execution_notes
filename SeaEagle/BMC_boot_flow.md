# BMC Boot Flow

## Boot Flow Diagram

```text
[Power On / Reset]
        |
        v
[SoC ROM code]
  - Hard-wired in silicon
  - Knows how to talk to SPI flash
        |
        v
[U-Boot bootloader in SPI NOR]
  - Lives in SPI NOR flash
  - Single, common bootloader
  - Has environment + boot logic
        |
        |---> Health checks / policy:
        |      - Is primary OS enabled?
        |      - Did previous boot fail too many times?
        |      - Integrity checks OK? (optional)
        |
        +-- if NORMAL BOOT path selected ----------------------+
        |                                                     |
        v                                                     |
[Load BMC-SONiC-OS from eMMC]                                |
  - Kernel + rootfs read from eMMC                           |
        |                                                     |
        v                                                     |
[Run BMC-SONiC-OS as main BMC OS]                            |
                                                             |
        +-- if RECOVERY / FALLBACK path selected ------------+
        |
        v
[Load golden OpenBMC from SPI NOR]
  - Minimal, known-good image
        |
        v
[Run golden OpenBMC (recovery environment)]
  - Used to repair / reflash eMMC
  - Can update main BMC-SONiC-OS image
```

## Boot Path Structure

**ROM** → **U-Boot (SPI NOR)** → either:
- **BMC-SONiC-OS** (eMMC, normal case), **or**
- **Golden OpenBMC** (SPI NOR, recovery case)

---

## Typical BMC-SONiC-OS Update Process

_This is a generic, high-level sequence; exact commands depend on your platform, but the responsibility split is the same._

### 1. Running System: BMC-SONiC-OS from eMMC

System is currently booted into BMC-SONiC-OS.

**Active storage:**
- **SPI NOR:** U-Boot + golden OpenBMC (unchanged)
- **eMMC:** active BMC-SONiC-OS rootfs + kernel

### 2. Fetch the New Image

From BMC-SONiC-OS, download the new firmware image via:
- HTTP(S)
- SCP
- Local USB
- An internal package repo

Store the update image in a temporary location on eMMC (or RAM) but **do not touch SPI NOR**.

### 3. Verify the Image

Still in BMC-SONiC-OS, perform checks:
- Signature verification (if supported)
- Hash / checksum verification
- Version compatibility checks (optional)

**If verification fails** → abort update; no changes have been made to SPI NOR or the running image.

### 4. Write the New BMC-SONiC-OS to eMMC

The updater writes the new OS image to the BMC-SONiC partition(s) on eMMC.

Often this is done with an **A/B scheme:**
- **eMMC-Boot-A** (current)
- **eMMC-Boot-B** (new)

The updater writes to the “inactive” slot to avoid corrupting the currently running one.

**SPI NOR is typically not modified:**
- U-Boot stays the same
- Golden OpenBMC stays the same as the backup path

### 5. Update U-Boot Environment (if using A/B or flags)
In many designs, BMC-SONiC-OS will tell U-Boot what to boot next by:

**Setting an environment variable** in U-Boot’s env storage (could be in SPI NOR or a small area on eMMC), such as:

- `boot_target = SONiC_A` or `SONiC_B`
- Possibly setting a “boot attempt counter” or “pending update” flag

This tells U-Boot: “On next reboot, try this new BMC-SONiC slot.”

### 6. Reboot into the New Image

Initiate a reboot from BMC-SONiC-OS.

On restart, the sequence is:
1. ROM → U-Boot from SPI NOR
2. U-Boot reads its environment and sees the selected BMC-SONiC-OS slot / image on eMMC
3. U-Boot loads the new kernel + rootfs from eMMC
4. System boots into the new BMC-SONiC-OS

### 7. Health Check and Success Path
After boot, either U-Boot or BMC-SONiC-OS performs health checks, for example:

- Did the OS reach a certain “ready” state in time?

- Did the OS clear a “pending update” flag?

- Did watchdogs stop firing?


**If everything looks good:**

- BMC-SONiC-OS or a small agent marks the new slot as “good”

- U-Boot’s env is updated so that this slot is now the primary

### 8. Failure and Automatic Fallback

**If something goes wrong:**

**Example failures:**
- The new BMC-SONiC-OS on eMMC does not boot
- It repeatedly crashes early
- It fails integrity checks

**U-Boot logic detects failures by:**
- Counting consecutive failed boots
- Not seeing a “boot OK” flag being set

**After N failed attempts:**
- U-Boot stops trying the broken BMC-SONiC-OS on eMMC
- It switches to the recovery path and boots the golden OpenBMC image from SPI NOR instead

**In golden OpenBMC:**

You have a known-good environment to:
- Inspect logs
- Reflash or roll back eMMC
- Retry the update with a different image

### 9. Key Points About What Gets Touched
**During a normal BMC-SONiC upgrade:**


- **eMMC:** updated (new OS image, maybe A/B slot changes).

- **SPI NOR:**

  - **U-Boot:** unchanged

  - **Golden OpenBMC:** unchanged

  - Possibly a small env area is modified (boot flags/variables), but core images remain intact.

This keeps the bootloader + golden recovery path stable and trusted while allowing frequent updates of your main, feature-rich BMC-SONiC-OS on eMMC.


---

## Glossary

### SPI NOR

**Stands for:**

- **SPI** = Serial Peripheral Interface
- **NOR** = NOR-type flash memory (a specific internal cell architecture)

**What it is (in this context)**:
A small, reliable flash chip connected over the SPI bus. It typically stores:

- The U-Boot bootloader
- A golden (recovery) OpenBMC image
Because it’s simple, robust, and usually not updated often, it’s ideal for critical boot and recovery code.

### eMMC

**Stands for:**
- **eMMC** = embedded MultiMediaCard

**What it is (in this context)**:
An on-board, higher-capacity flash storage device with a built‑in controller (like a tiny SSD soldered on the board). It stores:

- The main BMC-SONiC-OS image (kernel + root filesystem, etc.)
- Potentially logs, configs, and other runtime data
It’s used for the primary, feature-rich BMC OS that can be updated more frequently.