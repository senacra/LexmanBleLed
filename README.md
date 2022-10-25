# Lexman BLE LED

A Home Assistant integration for controlling bluetooth low energy led drivers
that natively use the Enki app.

## Configuration

Find the MAC address of each controller (eg using `hcitool lescan`)

Enter each controller as a light entity in your `configuration.yml`

```yaml
light:
  - platform: lexman_ble_led
    address: FF:FF:01:23:45:67
    name: Kitchen Worktop
```
