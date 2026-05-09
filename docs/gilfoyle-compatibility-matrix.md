# Gilfoyle Template & Variable Set Compatibility Matrix

## Quick Reference

| Template Name | Template ID | Compatible Variable Sets | OS Type | Use Case |
|---------------|-------------|--------------------------|---------|----------|
| `linux-node-testing-template` | `93` | `gcp-linux-vm-vs-qa-swapnil` (62) | Linux - REDHAT,ROCKY | QA testing |
| `linux-node-testing-template-allure` | `` | `gcp-linux-vm-vs-qa-swapnil` () | Linux - REDHAT,ROCKY| Generate Allure Results testing |
| `linux-node-testing-template-installer` | `` | `gcp-linux-vm-vs-qa-swapnil` () | Linux - REDHAT,ROCKY | Run only Installer test |
| `linux-node-testing-template` | `93` | `gcp-linux-vm-vs-qa-swapnil-deb2404` (62) | Linux - UBUNTU | QA testing |
| `linux-node-testing-template-allure` | `` | `gcp-linux-vm-vs-qa-swapnil-deb2404` () | Linux - UBUNTU| Generate Allure Results testing |
| `linux-node-testing-template-installer` | `` | `gcp-linux-vm-vs-qa-swapnil-deb2404` () | Linux - UBUNTU | Run only Installer test |
| `linux-node-testing-template` | `93` | `gcp-linux-vm-vs-qa-swapnil-deb2204` (62) | Linux - UBUNTU | QA testing |
| `linux-node-testing-template-allure` | `` | `gcp-linux-vm-vs-qa-swapnil-deb2204` () | Linux - UBUNTU| Generate Allure Results testing |
| `linux-node-testing-template-installer` | `` | `gcp-linux-vm-vs-qa-swapnil-deb2204` () | Linux - UBUNTU | Run only Installer test |

## Environment Variables Sets

| Variable Set | ID | Environment | Machine Type | Disk Size |
|--------------|----|-----------|--------------|-----------| 
| `gcp-linux-vm-vs-qa-swapnil` | `62` | QA | e2-standard-2 | 50GB |
| `gcp-windows-vs-qa` | `91` | QA | e2-standard-4 | 100GB |
| `gcp-ubuntu-vs-dev` | `75` | DEV | e2-medium | 30GB |
| `gcp-rhel-vs-staging` | `83` | STAGING | e2-standard-2 | 50GB |

## Usage Examples

```bash
# Linux QA
python scripts/create_run.py -t linux-node-testing-template -v gcp-linux-vm-vs-qa-swapnil -e test-pipeline-qa-swapnil -n 1.1.4

# Windows QA  
python scripts/create_run.py -t gcp-win2022-test-james -v gcp-windows-vs-qa -e windows-test-pipeline -n 2.0.1

# Ubuntu Dev
python scripts/create_run.py -t ubuntu-node-template -v gcp-ubuntu-vs-dev -e dev-testing -n 1.2.0-beta
```

## Required Variables

**Linux Templates:**
- `node_version`, `vm_name`, `machine_type`, `project_id`

**Windows Templates:**  
- `node_version`, `vm_name`, `machine_type`, `project_id`

## VM Naming Pattern
`pyautomator-{node_version}-{random_4digit}`

Example: `pyautomator-1-1-4-7832`